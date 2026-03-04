import logging
import asyncio
import aiofiles
from pathlib import Path
from typing import List, Dict, Tuple, Any

from app.core.parser.ast.models import (
    BaseNode,
    ClassNode as ASTClassNode,
    FunctionNode as ASTFunctionNode
)
from app.core.model.nodes import FileNode, ProjectNode, FunctionNode, ClassNode
from app.core.parser.ast.scanner import scan
from app.core.parser.jedi_adapter.manager import JediProjectManager
from app.core.repository import Repositories
from app.core.parser.graph_builder.performance import tracker

# IMPORT YOUR NEW BUILDER
from app.core.parser.graph_builder.call_graph.builder import CallChainBuilder

from app.core.model.schemas import CallSchema, CodeElementGroupSchema, CallGroupSchema

logger = logging.getLogger(__name__)


class BodyParser:
    def __init__(
        self,
        project_node: ProjectNode,
        repos: Repositories,
        jedi_manager: JediProjectManager,
        batch_size: int = 1000,
        progress_tracker=None,
    ):
        self.project_node = project_node
        self.project_path = Path(project_node.path)
        self.repos = repos
        self.progress_tracker = progress_tracker
        self.batch_size = batch_size

        # Global batch buffers (shared across all files)
        self._insert_buffer: List[Any] = []
        self._move_buffer: List[Tuple[str, str, str]] = []
        self._delete_buffer: List[str] = []
        self._batch_lock = asyncio.Lock()

        # Initialize the NEW Builder here
        self.call_chain_builder = CallChainBuilder(
            project_node=project_node,
            repos=repos,
            jedi_manager=jedi_manager
        )

    def _should_flush(self) -> bool:
        """True if any buffer has reached batch_size."""
        return (
            len(self._insert_buffer)+len(self._move_buffer) +
            len(self._delete_buffer) >= self.batch_size

        )

    async def _flush_buffers(self) -> None:
        """Flush all buffered inserts, deletes, and moves to the database."""
        async with self._batch_lock:
            if not self._insert_buffer and not self._delete_buffer and not self._move_buffer:
                return
            inserts = self._insert_buffer.copy()
            deletes = self._delete_buffer.copy()
            moves = self._move_buffer.copy()
            self._insert_buffer.clear()
            self._delete_buffer.clear()
            self._move_buffer.clear()
        await self.call_chain_builder.call_service.flush_batch(inserts, deletes, moves)

    async def _add_batch(
        self,
        inserts: List[Any] = None,
        moves: List[Tuple[str, str, str]] = None,
        deletes: List[str] = None,
    ) -> None:
        """Add inserts, moves, and deletes to buffers; flush if batch size reached."""
        inserts = inserts or []
        moves = moves or []
        deletes = deletes or []
        if not inserts and not moves and not deletes:
            return
        async with self._batch_lock:
            self._insert_buffer.extend(inserts)
            self._move_buffer.extend(moves)
            self._delete_buffer.extend(deletes)
            if self._should_flush():
                to_insert = self._insert_buffer.copy()
                to_delete = self._delete_buffer.copy()
                to_move = self._move_buffer.copy()
                self._insert_buffer.clear()
                self._delete_buffer.clear()
                self._move_buffer.clear()
            else:
                to_insert = to_delete = to_move = []
        if to_insert or to_delete or to_move:
            await self.call_chain_builder.call_service.flush_batch(
                to_insert, to_delete, to_move
            )

    async def flush_buffers(self) -> None:
        """Flush any remaining buffered operations. Call after all files are processed."""
        await self._flush_buffers()

    async def process_ast(self, file_node: FileNode):
        """
        Phase 2: Analyze the AST tree.
        Traverses the tree, finds DB nodes, and delegates call processing to CallChainBuilder.
        """
        file_path = Path(file_node.path)
        if not file_path.is_absolute():
            file_path = self.project_path / file_path

        # 1. Prefetch DB nodes (Optimization)
        existing_tree = await self.repos.file_repo.get_children(
            file_node.id,
            exclude_types=[CallSchema.__name__,
                           CodeElementGroupSchema.__name__,
                           CallGroupSchema.__name__,],
        )

        node_map: Dict[str, any] = {file_node.qname: file_node}

        for node in existing_tree:
            node_map[node.qname] = node

        # 2. Read Source
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as source:
                content = await source.read()
        except OSError:
            return

        # 3. Scan AST
        loop = asyncio.get_event_loop()
        try:
            nodes, processed_content = await loop.run_in_executor(
                None, scan, content, str(file_path)
            )
        except Exception:
            return

        # 4. Traverse and delegate to Builder
        await self._traverse_and_process(
            nodes,
            file_node,
            node_map,
            file_path=file_path,
            source=processed_content
        )

    def _traverse_and_collect(
        self,
        nodes: List[BaseNode],
        current_scope: any,
        node_map: Dict[str, any],
        file_path: Path,
        source: str,
    ) -> List[tuple]:
        """
        Sync traversal to collect all scopes (node, file_path, source) that need processing.
        """

        calls = []
        for node in nodes:
            if node.type == 'call':
                calls.append(node)

        items = [(current_scope, file_path, source, calls)]

        for node in nodes:
            if isinstance(node, (ASTClassNode, ASTFunctionNode)):
                qname = f"{current_scope.qname}.{node.name}"
                db_node = node_map.get(qname)

                if not db_node:
                    continue

                if hasattr(node, "children"):
                    items.extend(
                        self._traverse_and_collect(
                            node.children,
                            db_node,
                            node_map,
                            file_path,
                            source,
                        )
                    )

        return items

    async def _traverse_and_process(
        self,
        nodes: List[BaseNode],
        current_scope: any,
        node_map: Dict[str, any],
        file_path: Path,
        source: str,
    ):
        """
        Collect all scopes via sync traversal, then run process_node_scope for each in parallel.
        """
        items = self._traverse_and_collect(
            nodes, current_scope, node_map, file_path, source
        )

        async def _process_one(node: any, fp: Path, src: str, calls: List[Any]):
            if isinstance(node, (FunctionNode, ClassNode)) and self.progress_tracker:
                self.progress_tracker.set_current_function(node.qname)
                await self.progress_tracker.emit()
            try:
                results = await self.call_chain_builder.resolve_call_hierarchy(fp, node, calls)

                await self._add_batch(
                    inserts=results.calls_to_create,
                    moves=results.moves_to_execute,
                    deletes=results.call_ids_to_remove,
                )

            except Exception as e:
                print(f"Error processing node {node.qname}: {e}")
                raise e

            if isinstance(node, (FunctionNode, ClassNode)) and self.progress_tracker:
                self.progress_tracker.increment_entity_processed()
                self.progress_tracker.clear_current_function()

        semaphore = asyncio.Semaphore(3)

        async def bounded_process(n, fp, s, c):
            async with semaphore:
                return await _process_one(n, fp, s, c)

        await asyncio.gather(*[bounded_process(n, fp, s, c) for n, fp, s, c in items], return_exceptions=True)

        # NOTE: Per-file flush removed. PhaseProcessor calls body_parser.flush_buffers()
        # after all files are processed to send one final batch.
