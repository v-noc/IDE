import asyncio
import aiofiles
import logging
from pathlib import Path
from typing import Set, Dict, List, Optional
from collections import deque

from app.core.parser.ast.models import (
    BaseNode,
    ClassNode as ASTClassNode,
    FunctionNode as ASTFunctionNode
)
from app.core.model.nodes import FunctionNode, ClassNode, ContainerNode
from app.core.parser.ast.scanner import scan
from app.core.parser.ast.models import CallNode as ASTCallNode
from app.core.repository import Repositories
from app.core.parser.jedi_adapter.manager import JediProjectManager


from .resolver import CallResolverService
from .processor import ScopeProcessor
from .repository_extension import CallGraphRepository

logger = logging.getLogger(__name__)


class CallChainBuilder:
    def __init__(
        self,
        project_path: Path,
        repos: Repositories,
        jedi_manager: JediProjectManager,
        max_depth: int = 10
    ):
        self.project_path = project_path
        self.repos = repos

        # Helper services
        self.graph_repo = CallGraphRepository(repos.db)
        self.resolver = CallResolverService(jedi_manager, repos)
        self.processor = ScopeProcessor(self.graph_repo)

        self.max_depth = max_depth

    async def build_full_chain(self, start_node: ContainerNode):
        """
        Starts a recursive BFS process to build the call chain starting from start_node.
        """
        visited_ids: Set[str] = {start_node.id}
        queue = deque([(start_node, 0)])  # (node, depth)

        logger.info(f"Starting recursive call build for {start_node.qname}")

        while queue:
            current_node, depth = queue.popleft()

            if depth >= self.max_depth:
                continue

            # 1. Process this specific node (Scope)
            active_targets = await self._process_single_scope(current_node)

            # 2. Add children to queue
            # Only add targets we haven't processed in this session yet to avoid infinite loops
            # and to handle recursion properly.

            # We need to fetch the actual Node objects for these target IDs to process them
            if active_targets:
                target_nodes = await self._fetch_nodes_batch(list(active_targets))

                for node in target_nodes:
                    if node.id not in visited_ids:
                        visited_ids.add(node.id)
                        queue.append((node, depth + 1))

    async def _process_single_scope(self, node: ContainerNode) -> Set[str]:
        """
        Reads file, scans AST, Resolves Calls, Syncs DB.
        Returns: Set of target_ids referenced in this scope.
        """
        # 1. Get Source Code
        file_info = await self.repos.nodes.get_nearest_file_and_project(node.id)
        if not file_info or not file_info.get("file"):
            return set()

        file_path_str = file_info["file"]["path"]
        abs_path = self.project_path / \
            file_path_str if not Path(
                file_path_str).is_absolute() else Path(file_path_str)

        try:
            async with aiofiles.open(abs_path, "r", encoding="utf-8") as f:
                source = await f.read()
        except OSError:
            logger.error(f"Could not read source for {node.qname}")
            return set()

        # 2. Parse AST for THIS scope
        # Note: 'scan' gives us the whole file. We need to filter for the specific function body.
        # Ideally, your AST parser supports getting a subtree. If not, we scan the whole file
        # and traverse to find the node matching current_node.name/qname.

        # Assuming we have a helper to get AST body for a specific function:
        ast_calls = await self._extract_calls_from_source(source, abs_path, node)

        # 3. Resolve Calls
        resolved = await self.resolver.resolve_scope_calls(abs_path, source, ast_calls)

        # 4. Sync to DB (Create/Delete)
        result = await self.processor.sync_scope(node, resolved)

        return result.all_active_targets

    async def _extract_calls_from_source(
        self,
        source: str,
        path: Path,
        target_node: ContainerNode
    ) -> List[ASTCallNode]:
        """
        Scans file and extracts AST CallNodes specifically belonging to target_node's body.
        Excludes calls belonging to nested functions/classes defined within.
        """
        # 1. Scan the AST
        loop = asyncio.get_event_loop()
        nodes, _ = await loop.run_in_executor(None, scan, source, str(path))

        found_calls: List[ASTCallNode] = []

        # We need the start line to identify the correct AST node
        target_line = target_node.position.line_no if target_node.position else 0

        # Strategy:
        # 1. Find the AST node that corresponds to our target_node
        # 2. Traverse ONLY that node's children to find calls
        # 3. Do not enter nested Function/Class definitions

        def _find_target_ast_node(node_list: List[BaseNode]) -> Optional[BaseNode]:
            """Recursively finds the AST node matching the target's line number."""
            for node in node_list:
                # Check if this node matches our target (Class or Function)
                if isinstance(node, (ASTClassNode, ASTFunctionNode)):
                    if node.position and node.position.line == target_line:
                        return node

                # If this node contains our target (based on lines), recurse down
                if hasattr(node, "children"):
                    # Optimization: Only look inside if target line is within this node's range
                    # (Assuming node.position has end_line, otherwise just recurse)
                    if hasattr(node, "position") and node.position:
                        if node.position.line <= target_line <= node.position.end_line:
                            found = _find_target_ast_node(node.children)
                            if found:
                                return found
                    else:
                        # Fallback for nodes without clear range
                        found = _find_target_ast_node(node.children)
                        if found:
                            return found
            return None

        def _collect_direct_calls(node_list: List[BaseNode]):
            """Collects calls in current scope, recursing into blocks (if/while) but NOT definitions."""
            for node in node_list:
                if isinstance(node, ASTCallNode):
                    found_calls.append(node)

                # Check children
                if hasattr(node, "children"):
                    # STOP recursion if we hit a scope boundary (another function/class)
                    if isinstance(node, (ASTClassNode, ASTFunctionNode)):
                        continue

                    # Continue recursion for structural nodes (If, Else, Try, For, While, etc.)
                    _collect_direct_calls(node.children)

        # Execution Logic
        target_ast_node = None

        # Case A: target_node is the File itself
        if target_node.node_type == "file":
            _collect_direct_calls(nodes)
        else:
            # Case B: target_node is a Function or Class
            target_ast_node = _find_target_ast_node(nodes)

            if target_ast_node and hasattr(target_ast_node, "children"):
                _collect_direct_calls(target_ast_node.children)
            else:
                # Log warning: Could not map DB node to AST node (out of sync?)
                pass

        return found_calls

    async def _fetch_nodes_batch(self, node_ids: List[str]) -> List[ContainerNode]:
        """Fetch multiple nodes from DB."""
        # You can implement a batch fetch in NodeRepo
        results = []
        for nid in node_ids:
            # Try function
            n = await self.repos.function_repo.get_by_id(nid)
            if not n:
                n = await self.repos.class_repo.get_by_id(nid)
            if n:
                results.append(n)
        return results

    async def _load_node_context(self, node: ContainerNode):
        """Helper to load file path and source code for a DB node."""

        file_info = await self.repos.nodes.get_nearest_file_and_project(node.id)

        if not file_info or not file_info.get("file"):
            return None, None

        file_path_str = file_info["file"]["path"]
        abs_path = self.project_path / \
            file_path_str if not Path(
                file_path_str).is_absolute() else Path(file_path_str)

        try:
            async with aiofiles.open(abs_path, "r", encoding="utf-8") as f:
                source = await f.read()
            return abs_path, source
        except OSError:
            logger.error(f"Could not read source for {node.qname}")
            return None, None

    async def process_node_scope(
        self,
        node: ContainerNode,
        file_path: Optional[Path] = None,
        source_code: Optional[str] = None,
        visited_ids: Optional[Set[str]] = None,
        current_depth: int = 0
    ):
        """
        Public entry point for BodyParser.
        Analyzes a specific node's body using provided source code.
        """
        # 0. Recursion Guard
        if visited_ids is None:
            visited_ids = set()

        if node.id in visited_ids:
            return
        visited_ids.add(node.id)

        if current_depth >= self.max_depth:
            return

        # 1. Load Context (File & Source)
        # If not provided (recursive step), we must load it.
        if not file_path or not source_code:
            file_path, source_code = await self._load_node_context(node)
            print(f"file_path: {file_path}")

            if not file_path:
                return

        # 1. Extract AST calls specifically for this node's range
        # (You implement _extract_calls_from_source as discussed previously)
        ast_calls = await self._extract_calls_from_source(source_code, file_path, node)

        # 2. Resolve calls in parallel
        resolved = await self.resolver.resolve_scope_calls(file_path, source_code, ast_calls)

        # 3. Sync to DB (Batch Create/Delete)
        sync_result = await self.processor.sync_scope(node, resolved)

        # =========================================================
        # THE SPIDER LOGIC (Replicating your old logic)
        # =========================================================
        # We found targets (B, C). Now we must process THEM immediately.

        target_ids_to_recurse = sync_result.all_active_targets

        # if target_ids_to_recurse:
        #     # Fetch the actual Node objects for B and C
        #     target_nodes = await self._fetch_nodes_batch(list(target_ids_to_recurse))

        #     for target_node in target_nodes:
        #         # RECURSION: Process B immediately
        #         # Note: We pass None for file/source to force re-loading context for the new node
        #         await self.process_node_scope(
        #             node=target_node,
        #             file_path=None,
        #             source_code=None,
        #             visited_ids=visited_ids,
        #             current_depth=current_depth + 1
        #         )
