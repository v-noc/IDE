import logging
import asyncio
import aiofiles
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional

from app.core.parser.ast.models import (
    BaseNode,
    ClassNode as ASTClassNode,
    FunctionNode as ASTFunctionNode
)
from app.core.model.nodes import CallNode, FileNode, ProjectNode, FunctionNode, ClassNode
from app.core.parser.drivers import DriverManager
from app.core.repository import Repositories
from app.core.parser.graph_builder.performance import tracker

from app.core.parser.graph_builder.call_graph.builder import CallChainBuilder
from app.core.call_insert_order import toposort_calls_for_insert

from app.core.model.schemas import CallSchema, CodeElementGroupSchema, CallGroupSchema

logger = logging.getLogger(__name__)

_INSERT_FLUSH_THRESHOLD = 50_000
_DELETE_MOVE_FLUSH_THRESHOLD = 5_000
_INSERT_CHUNK_SIZE = 60_000
_DELETE_MOVE_CHUNK_SIZE = 5_000


class BodyParser:
    def __init__(
        self,
        project_node: ProjectNode,
        repos: Repositories,
        driver_manager: DriverManager,
        batch_size: int = 1000,
        progress_tracker=None,
    ):
        self.project_node = project_node
        self.project_path = Path(project_node.path)
        self.repos = repos
        self.progress_tracker = progress_tracker
        self._insert_flush_threshold = _INSERT_FLUSH_THRESHOLD
        self._delete_move_flush_threshold = _DELETE_MOVE_FLUSH_THRESHOLD
        self._insert_chunk_size = _INSERT_CHUNK_SIZE
        self._delete_move_chunk_size = _DELETE_MOVE_CHUNK_SIZE

        # Global batch buffers (shared across all files)
        self._insert_buffer: List[CallNode] = []
        self._move_buffer: List[Tuple[str, str, str]] = []
        self._delete_buffer: List[str] = []
        self._batch_lock = asyncio.Lock()

        self.call_chain_builder = CallChainBuilder(
            project_node=project_node,
            repos=repos,
            driver_manager=driver_manager,
        )

    async def _flush_inserts(self, inserts: List[CallNode]) -> None:
        if not inserts:
            return

        ordered = toposort_calls_for_insert(inserts)
        for i in range(0, len(ordered), self._insert_chunk_size):
            chunk = ordered[i: i + self._insert_chunk_size]
            result = await self.repos.call_repo.create(chunk)
            if result is None:
                logger.error(
                    "Call insert chunk failed (%s nodes starting at %s)",
                    len(chunk),
                    i,
                )

    async def _flush_buffers(self) -> None:
        """Drain buffers: inserts first, then delete+move (independent of each other)."""
        async with self._batch_lock:
            if not self._insert_buffer and not self._delete_buffer and not self._move_buffer:
                return
            inserts = self._insert_buffer.copy()
            deletes = self._delete_buffer.copy()
            moves = self._move_buffer.copy()
            self._insert_buffer.clear()
            self._delete_buffer.clear()
            self._move_buffer.clear()

        if inserts:
            await self._flush_inserts(inserts)
        if deletes or moves:
            await self.repos.call_repo.flush_delete_move_batch_chunked(
                deletes,
                moves,
                insert_ids=None,
                chunk_size=self._delete_move_chunk_size,
            )

    async def _add_batch(
        self,
        inserts: List[CallNode] = None,
        moves: List[Tuple[str, str, str]] = None,
        deletes: List[str] = None,
    ) -> None:
        """Add to buffers; flush inserts and delete+move independently when thresholds hit."""
        inserts = inserts or []
        moves = moves or []
        deletes = deletes or []

        logger.debug(
            "call batch buffer +%s inserts, +%s moves, +%s deletes (buf i/m/d=%s/%s/%s)",
            len(inserts),
            len(moves),
            len(deletes),
            len(self._insert_buffer),
            len(self._move_buffer),
            len(self._delete_buffer),
        )
        if not inserts and not moves and not deletes:
            return

        inserts_to_flush: List[CallNode] | None = None
        dm_to_flush: Tuple[List[str], List[Tuple[str, str, str]]] | None = None

        async with self._batch_lock:
            self._insert_buffer.extend(inserts)
            self._move_buffer.extend(moves)
            self._delete_buffer.extend(deletes)

            if len(self._insert_buffer) >= self._insert_flush_threshold:
                inserts_to_flush = self._insert_buffer.copy()
                self._insert_buffer.clear()

            if (
                len(self._delete_buffer) >= self._delete_move_flush_threshold
                or len(self._move_buffer) >= self._delete_move_flush_threshold
            ):
                dm_to_flush = (
                    self._delete_buffer.copy(),
                    self._move_buffer.copy(),
                )
                self._delete_buffer.clear()
                self._move_buffer.clear()

        if inserts_to_flush:
            await self._flush_inserts(inserts_to_flush)

        if dm_to_flush:
            deletes_f, moves_f = dm_to_flush
            insert_ids = (
                {n.id for n in inserts_to_flush} if inserts_to_flush else None
            )
            await self.repos.call_repo.flush_delete_move_batch_chunked(
                deletes_f,
                moves_f,
                insert_ids=insert_ids,
                chunk_size=self._delete_move_chunk_size,
            )

    async def flush_buffers(self) -> None:
        """Flush any remaining buffered operations. Call after all files are processed."""
        await self._flush_buffers()

    async def process_ast(self, file_node: FileNode, content: Optional[str] = None):
        """
        Phase 2: Analyze the AST tree.
        Traverses the tree, finds DB nodes, and delegates call processing to CallChainBuilder.
        If content is provided (from Phase 1), skips file read to avoid duplicate I/O.
        """
        file_path = Path(file_node.path)
        if not file_path.is_absolute():
            file_path = self.project_path / file_path

        # 1. Prefetch DB nodes (Optimization)
        existing_tree = await self.repos.structure_repo.get_children(
            file_node.id,
            exclude_types=[CallSchema.__name__,
                           CodeElementGroupSchema.__name__,
                           CallGroupSchema.__name__,],

        )

        node_map: Dict[str, any] = {file_node.qname: file_node}

        for node in existing_tree:
            node_map[node.qname] = node

        # 2. Read Source (skip if content provided from Phase 1)
        if content is None:
            try:
                async with aiofiles.open(file_path, "r", encoding="utf-8") as source:
                    content = await source.read()
            except OSError:
                return

        # 3. Parse AST (Phase 2: no MRO)
        try:
            driver = await self.call_chain_builder.driver_manager.get_driver(
                str(file_path)
            )
            parse_result = await driver.parse_file(
                str(file_path), content, resolve_mro=False
            )
            nodes, processed_content = parse_result.nodes, parse_result.content
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
        print(f"started processing {len(items)} nodes in file {file_path}")

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

        semaphore = asyncio.Semaphore(1)

        async def bounded_process(n, fp, s, c):
            async with semaphore:
                return await _process_one(n, fp, s, c)

        await asyncio.gather(*[bounded_process(n, fp, s, c) for n, fp, s, c in items], return_exceptions=True)

        # NOTE: Per-file flush removed. PhaseProcessor calls body_parser.flush_buffers()
        # after all files are processed to send one final batch.
