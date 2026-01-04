import asyncio
import aiofiles
import logging
from pathlib import Path
from typing import Any, Set, Dict, List, Optional
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
        Only returns **direct-child** calls for the given scope:
        - file: calls that appear at module level (not inside any class/function)
        - class: calls that appear directly in the class body (not inside methods/nested defs)
        - function: calls that appear directly in the function body (not inside nested defs)
        """
        # 1. Scan the AST
        loop = asyncio.get_event_loop()
        nodes, _ = await loop.run_in_executor(None, scan, source, str(path))

        def _normalize_id(raw: Optional[str]) -> Optional[str]:
            if not raw:
                return None
            # DB ids are often like "nodes/<uuid>" while AST ids are "<uuid>"
            return raw.split("/")[-1]

        def _iter_scopes(node_list: List[BaseNode]) -> List[BaseNode]:
            """Returns all AST class/function nodes in the tree (DFS)."""
            scopes: List[BaseNode] = []
            stack = list(node_list)
            while stack:
                n = stack.pop()
                if isinstance(n, (ASTClassNode, ASTFunctionNode)):
                    scopes.append(n)
                    # nested defs live in children
                    if getattr(n, "children", None):
                        stack.extend(n.children)
                else:
                    # We only expect children on class/function nodes, but keep safe.
                    if getattr(n, "children", None):
                        stack.extend(n.children)
            return scopes

        def _direct_calls(node_list: List[BaseNode]) -> List[ASTCallNode]:
            """Only direct children that are calls (no recursion)."""
            return [n for n in node_list if isinstance(n, ASTCallNode)]

        # Case A: file scope => top-level direct calls only
        if target_node.node_type == "file":
            return _direct_calls(nodes)

        # Case B: class/function scope => find matching AST scope node
        target_id = _normalize_id(getattr(target_node, "id", None))
        target_name = getattr(target_node, "name", None)
        target_line = target_node.position.line_no if getattr(
            target_node, "position", None) else None

        matched_scope: Optional[BaseNode] = None
        all_scopes = _iter_scopes(nodes)

        # 1) Prefer exact ID match when possible
        if target_id:
            for s in all_scopes:
                if _normalize_id(getattr(s, "id", None)) == target_id:
                    matched_scope = s
                    break

        # 2) Fallback to (name + start line)
        if not matched_scope and target_name and target_line is not None:
            for s in all_scopes:
                if getattr(s, "name", None) == target_name and getattr(s, "position", None):
                    if s.position.line == target_line:
                        matched_scope = s
                        break

        if not matched_scope:
            # Could not map DB node -> AST node (likely out of sync); return nothing.
            return []

        return _direct_calls(getattr(matched_scope, "children", []) or [])

    async def _fetch_nodes_batch(self, node_ids: List[str]) -> List[ContainerNode]:
        """Fetch multiple nodes from DB."""
        # You can implement a batch fetch in NodeRepo
        results = []
        for nid in node_ids:
            # Try function
            n = await self.repos.nodes.get_by_id(nid)

            if n:
                results.append(n)
        return results

    async def _load_node_context(self, node: ContainerNode):
        """Helper to load file path and source code for a DB node."""
        file_path_str = ""
        if node.node_type == "file":
            file_path_str = node.path

        else:
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
        parent_call_node_id: Optional[str] = None,
        visited_ids: Optional[Dict[str, int]] = None,
        current_depth: int = 0,
        parent_context: Optional[Any] = None
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
            file_path, source_code = await self._load_node_context(node)

            if not file_path:
                return

        ast_calls = await self._extract_calls_from_source(source_code, file_path, node)

        # 2. Resolve calls in parallel
        resolved, context_map = await self.resolver.resolve_scope_calls(file_path, source_code, ast_calls, parent_context=parent_context)

        # 3. Sync to DB (Batch Create/Delete)
        sync_result = await self.processor.sync_scope(node, resolved, parent_call_node_id=parent_call_node_id)

        # =========================================================
        # THE SPIDER LOGIC (Replicating your old logic)
        # =========================================================
        # We found targets (B, C). Now we must process THEM immediately.

        if sync_result.created_map:
            #     # Fetch the actual Node objects for B and C
            target_nodes = await self._fetch_nodes_batch(list(sync_result.created_map.keys()))

            for target_node in target_nodes:
                # RECURSION: Process B immediately
                next_step_context = context_map.get(target_node.id)
                await self.process_node_scope(
                    node=target_node,
                    parent_call_node_id=sync_result.created_map[target_node.id],
                    file_path=None,
                    source_code=None,
                    visited_ids=visited_ids.copy(),
                    current_depth=current_depth + 1,
                    parent_context=next_step_context
                )
