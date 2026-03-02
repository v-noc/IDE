import asyncio
import aiofiles
import logging
import os
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
        self.diff_calculator = DiffCalculator()
        self.semaphore = asyncio.Semaphore(1)

        self.max_depth = max_depth

    async def resolve_call_hierarchy(self, file_path: Path, node: any, calls: List[Any]) -> ScopeSyncResult:

        merged_stack = CallFrameStack(
            target_qname="root", target_id="root", children=[])

        async def resolve_one(call: Any) -> CallFrameStack:
            async with self.semaphore:
                return await asyncio.to_thread(
                    self.call_hierarchy_resolver.resolve_call_hierarchy,
                    str(file_path),
                    call,
                )

        returned_stacks = await asyncio.gather(*[resolve_one(call) for call in calls])
        for returned_stack in returned_stacks:
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
