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
from app.core.parser.graph_builder.performance import tracker
from app.core.services.call_service import CallService


from .resolver import CallResolverService
from .processor import ScopeProcessor

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
        self.resolver = CallResolverService(jedi_manager, repos)
        self.processor = ScopeProcessor(self.call_service)

        self.max_depth = max_depth

    async def _extract_calls_from_source(
        self,
        source: str,
        path: Path,
        target_node: any
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
        if isinstance(target_node, FileNode):
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

    async def _fetch_nodes_batch(self, node_ids: List[str]) -> List[any]:
        """Fetch multiple nodes from DB."""
        # You can implement a batch fetch in NodeRepo

        results = await self.repos.function_repo.get_by_ids(node_ids, self.project_node.db_name)

        return results

    async def _load_node_context(self, node: any):
        """Helper to load file path and source code for a DB node."""
        file_path_str = ""
        if isinstance(node, FileNode):
            file_path_str = node.path

        else:
            with tracker.timer("call_graph.load_node_context.get_nearest_file_and_project"):
                file_info = await self.repos.file_repo.get_parent_file(node.id, self.project_node.db_name)

                if not file_info:
                    return None, None

                file_path_str = file_info.path

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
                print("visited_ids reached")
                return
        else:
            visited_ids[node.id] = 1

        if current_depth >= self.max_depth:
            print("max depth reached")
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
        else:
            print(f"{node.id} - {file_path} all_resolved_map -{all_resolved_map}")


class TempNode:
    id: str
    qname: str

    def __init__(self, id: str, qname: str):
        self.id = id
        self.qname = qname
