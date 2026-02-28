import asyncio
import aiofiles
import logging
from pathlib import Path
from typing import Any, Awaitable, Callable, Set, Dict, List, Optional, Tuple
from collections import deque

from app.core.parser.ast.models import (
    BaseNode,
    ClassNode as ASTClassNode,
    FunctionNode as ASTFunctionNode
)
from app.core.model.nodes import ProjectNode, FileNode
from app.core.parser.ast.scanner import scan
from app.core.parser.ast.models import CallNode as ASTCallNode
from app.core.repository import Repositories
from app.core.parser.jedi_adapter.manager import JediProjectManager
from app.core.parser.graph_builder.call_graph.models import ResolvedCall
from app.core.parser.graph_builder.call_graph.models import ScopeSyncResult
from app.core.parser.graph_builder.performance import tracker
from app.core.services.call_service import CallService
from app.core.parser.jedi_adapter.call_resolver.call_resolver import CallFrameStack, CallHierarchyResolver
from app.core.builder.tree_builder import TreeBuilder

from .resolver import CallResolverService
from .processor import ScopeProcessor
from .diff_calulator import DiffCalculator

logger = logging.getLogger(__name__)


class CallChainBuilder:
    def __init__(
        self,
        project_node: ProjectNode,
        repos: Repositories,
        jedi_manager: JediProjectManager,
        max_depth: int = 10
    ):
        self.project_node = project_node
        self.project_path = Path(project_node.path)
        self.repos = repos

        # Helper services
        self.call_service = CallService(repos, project_node)
        self.call_hierarchy_resolver = CallHierarchyResolver(jedi_manager)
        self.resolver = CallResolverService(jedi_manager, repos)
        self.diff_calculator = DiffCalculator()

        self.max_depth = max_depth

    async def process_node_scope(
        self,
        node: any,
        file_path: Optional[Path] = None,
        source_code: Optional[str] = None,
        parent_call_node_id: Optional[str] = None,
        visited_ids: Optional[Dict[str, int]] = None,
        current_depth: int = 0,
        parent_contexts: List[Any] = [None],
        new_branch: Optional[str] = None,
        insert_batch_setter: Optional[Callable[[
            List[Any], Optional[str]], Awaitable[None]]] = None,
        move_batch_setter: Optional[Callable[[
            List[Tuple[str, str, str]]], Awaitable[None]]] = None,
    ):
        """
        Public entry point for BodyParser.
        Analyzes a specific node's body using provided source code.
        """
        # 0. Recursion Guard

        if visited_ids is None:
            visited_ids = {}

        if node.id in visited_ids:
            visited_ids[node.id] = visited_ids[node.id] + 1
            if visited_ids[node.id] > 2:
                return
        else:
            visited_ids[node.id] = 1

        if current_depth >= self.max_depth:
            return

        # 1. Load Context (File & Source)
        # If not provided (recursive step), we must load it.
        if not file_path or not source_code:
            with tracker.timer("call_graph.load_node_context"):
                file_path, source_code = await self._load_node_context(node)

            if not file_path:
                print(" no file path")
                return

        ast_calls = await self._extract_calls_from_source(source_code, file_path, node)

        # 2. Resolve calls in parallel (Merging Contexts)
        all_resolved_map: Dict[str, ResolvedCall] = {}
        merged_context_map: Dict[str, List[Any]] = {}

        # If parent_contexts is empty or None, treat as [None]
        if not parent_contexts:
            parent_contexts = [None]

        for ctx in parent_contexts:
            with tracker.timer("call_graph.resolve_scope_calls"):
                resolved_list, c_map = await self.resolver.resolve_scope_calls(
                    file_path, source_code, ast_calls, parent_context=ctx
                )

            # Merge Resolved Calls (Deduplicate by target_id)
            for r in resolved_list:
                all_resolved_map[r.target_id] = r

            # Merge Context Maps (Append list of contexts)
            for tid, ctx_list in c_map.items():
                if tid not in merged_context_map:
                    merged_context_map[tid] = []
                # ctx_list is now a list from the updated resolver
                merged_context_map[tid].extend(ctx_list)

        # 3. Sync to DB (Batch Create/Delete)
        # We pass the collected unique values
        with tracker.timer("call_graph.sync_scope"):

            sync_result = await self.processor.sync_scope(
                node,
                list(all_resolved_map.values()),
                parent_call_node_id=parent_call_node_id,
                new_branch=new_branch,
                insert_batch_setter=insert_batch_setter,
                move_batch_setter=move_batch_setter,
            )

        # =========================================================
        # THE SPIDER LOGIC (Replicating your old logic)
        # =========================================================
        # We found targets (B, C). Now we must process THEM immediately.

        if sync_result.created_map:
            # with tracker.timer("call_graph.fetch_nodes_batch"):
            #     target_nodes = await self._fetch_nodes_batch(list(sync_result.created_map.keys()))

            # Batch process all target nodes concurrently
            tasks = []
            for target_node in list(sync_result.created_map.keys()):
                # RECURSION: Process B immediately
                # Get the list of contexts for this target from our merged map
                next_step_contexts = merged_context_map.get(
                    target_node, [None])

                tasks.append(
                    self.process_node_scope(
                        node=TempNode(id=target_node, qname=target_node),
                        parent_call_node_id=sync_result.created_map[target_node],
                        file_path=None,
                        source_code=None,
                        visited_ids=visited_ids.copy(),
                        current_depth=current_depth + 1,
                        parent_contexts=next_step_contexts,
                        new_branch=new_branch,
                        insert_batch_setter=insert_batch_setter,
                        move_batch_setter=move_batch_setter,
                    )
                )

            # Execute all tasks concurrently
            if tasks:
                await asyncio.gather(*tasks)

            merged_context_map.clear()
        elif len(ast_calls) > 0:
            print(
                f"ast_calls: {file_path} - {(ast_calls)} resolved_list: {resolved_list}")

    async def resolve_call_hierarchy(self, file_path: Path, node: any, calls: List[Any]) -> ScopeSyncResult:

        merged_stack = CallFrameStack(
            target_qname="root", target_id="root", children=[])
        for call in calls:
            returned_stack = self.call_hierarchy_resolver.resolve_call_hierarchy(
                str(file_path), call)
            self._merge_frame_stack(merged_stack, returned_stack)

        old_children = await self.call_service.get_children(node.id)
        results = await self.preprocess_call_hierarchy(merged_stack, old_children, node.id)
        return results

    def _merge_frame_stack(self, target: CallFrameStack, source: CallFrameStack):
        """Merge source tree into target tree by target_id."""
        for source_child in source.children:
            matched = next(
                (c for c in target.children if c.target_id == source_child.target_id),
                None,
            )
            if not matched:
                matched = CallFrameStack(
                    target_qname=source_child.target_qname,
                    target_id=source_child.target_id,
                    children=[],
                )
                target.add_child(matched)
            self._merge_frame_stack(matched, source_child)

    async def preprocess_call_hierarchy(
        self,
        call_frame_stack: CallFrameStack,
        old_children: List[Any],
        root_parent_id: str,
    ) -> ScopeSyncResult:
        old_tree = TreeBuilder(old_children).build()
        return self.diff_calculator.calculate_diff(
            root_parent_id=root_parent_id,
            new_tree=call_frame_stack,
            old_tree=old_tree,
        )


class TempNode:
    id: str
    qname: str

    def __init__(self, id: str, qname: str):
        self.id = id
        self.qname = qname
