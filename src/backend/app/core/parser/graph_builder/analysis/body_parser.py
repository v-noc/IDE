import logging
import asyncio
import aiofiles
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

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

        # Initialize the NEW Builder here
        self.call_chain_builder = CallChainBuilder(
            project_node=project_node,
            repos=repos,
            jedi_manager=jedi_manager
        )

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
            project_db_name=self.project_node.db_name
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

        client = self.repos.client.clone()
        await client.set_db(self.project_node.db_name)

        insert_buffer: List[Tuple[Any, Optional[str]]] = []
        move_buffer: List[Tuple[str, str, str]] = []
        delete_buffer: List[str] = []
        batch_lock = asyncio.Lock()
        new_branch = f"main"
        # await client.create_branch(new_branch_id=new_branch)
        client.branch = new_branch

        async def _flush_buffers_locked():
            if delete_buffer:
                await self.call_chain_builder.call_service.batch_delete(delete_buffer.copy())
                delete_buffer.clear()

            if insert_buffer:
                grouped_inserts: Dict[Optional[str], List[Any]] = {}
                for call_node, branch_name in insert_buffer:
                    grouped_inserts.setdefault(
                        branch_name, []).append(call_node)

                for branch_name, calls in grouped_inserts.items():
                    await self.call_chain_builder.call_service.create_batch(
                        calls, branch_name=branch_name
                    )
                insert_buffer.clear()

            if move_buffer:

                await self.call_chain_builder.call_service.move_batch(move_buffer.copy(), branch_name=new_branch)

                move_buffer.clear()

        async def _set_insert_batch(calls: List[Any], branch_name: Optional[str]):

            if not calls:
                return
            async with batch_lock:
                insert_buffer.extend((call_node, branch_name)
                                     for call_node in calls)
                if len(insert_buffer) >= self.batch_size:
                    await _flush_buffers_locked()

        async def _set_move_batch(moves: List[Tuple[str, str, str]]):
            if not moves:
                return
            async with batch_lock:
                move_buffer.extend(moves)
                if len(move_buffer) >= self.batch_size:
                    await _flush_buffers_locked()

        async def _set_delete_batch(call_ids: List[str]):
            if not call_ids:
                return
            async with batch_lock:
                delete_buffer.extend(call_ids)
                if len(delete_buffer) >= self.batch_size:
                    await _flush_buffers_locked()

        async def _process_one(node: any, fp: Path, src: str, calls: List[Any]):
            if isinstance(node, (FunctionNode, ClassNode)) and self.progress_tracker:
                self.progress_tracker.set_current_function(node.qname)
                await self.progress_tracker.emit()
            try:
                results = await self.call_chain_builder.resolve_call_hierarchy(fp, node, calls)
                await _set_insert_batch(results.calls_to_create, new_branch)
                await _set_move_batch(results.moves_to_execute)
                await _set_delete_batch(results.call_ids_to_remove)

                # for call_id in results.call_ids_to_remove:
                #     await self.call_chain_builder.call_service.delete(call_id)

            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Error processing node {node.qname}: {e}")
                raise e

            if isinstance(node, (FunctionNode, ClassNode)) and self.progress_tracker:
                self.progress_tracker.increment_entity_processed()
                self.progress_tracker.clear_current_function()
                # await self.progress_tracker.emit()

        semaphore = asyncio.Semaphore(3)

        async def bounded_process(n, fp, s, c):
            async with semaphore:
                return await _process_one(n, fp, s, c)
        await asyncio.gather(*[bounded_process(n, fp, s, c) for n, fp, s, c in items], return_exceptions=True)

        async with batch_lock:
            await _flush_buffers_locked()

        # await client.squash("Squash commit for " + current_scope.qname, branch_name=new_branch)

        # result = await client.apply(before_version="main", after_version=new_branch, branch="main")
        # print(f"Apply result: {result}")
        # await client.delete_branch(new_branch)
