import logging
import asyncio
import aiofiles
import uuid
from pathlib import Path

from typing import List, Optional

from app.core.parser.ast.models import BaseNode, CallNode, ClassNode, FunctionNode
from app.core.parser.ast.scanner import scan
from app.core.parser.graph_builder.analysis.call_chain_builder import CallChainBuilder
from app.core.parser.jedi_adapter.manager import JediProjectManager
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeModel
from app.core.parser.graph_builder.performance import tracker

logger = logging.getLogger(__name__)


class BodyParser:
    def __init__(
        self,
        project_path: Path,
        project_name: str,
        scope_manager: ScopeManager,
        jedi_manager: JediProjectManager,
        batch_size: int = 1000,
        call_resolve_concurrency: int = 8,
    ):
        self.project_path = project_path
        self.project_name = project_name
        self.manager = scope_manager
        self.jedi_manager = jedi_manager
        self.batch_size = batch_size
        self.call_resolve_concurrency = call_resolve_concurrency
        self.processed_scope_ids = set()
        # Initialize CallChainBuilder for recursive call resolution
        self.call_chain_builder = CallChainBuilder(
            project_path=project_path,
            project_name=project_name,
            scope_manager=scope_manager,
            jedi_manager=jedi_manager,
        )

    async def flush_all_call_sites(self):
        """Flush call sites and return processed scope IDs."""
        with tracker.timer("body_parser.flush_all_call_sites"):
            await self.call_chain_builder.flush_all_call_sites()
        return self.processed_scope_ids.copy()

    def get_stats(self) -> dict:
        """Get statistics from the CallChainBuilder."""
        return self.call_chain_builder.get_stats()

    async def process_ast(self, file_scope: ScopeModel):
        """
        Phase 2: Analyze the AST tree for calls.
        Traverses the tree, entering scopes (Function/Class) as encountered.
        """
        with tracker.timer("body_parser.process_ast_total"):
            file_path = Path(file_scope.file_path)
            if not file_path.is_absolute():
                file_path = Path(self.project_path) / file_path

            # Prefetch all scopes and clear calls in batch
            with tracker.timer("body_parser.prefetch_and_clear"):
                descendants = await self.manager.get_descendants(file_scope.id)
                all_scopes = [file_scope] + descendants
                scope_map = {s.id: s for s in all_scopes}

                with tracker.timer("body_parser.batch_clear_calls"):
                    await self.manager.batch_clear_calls(list(scope_map.keys()))

            try:
                with tracker.timer("body_parser.read_file"):
                    async with aiofiles.open(file_path, "r", encoding="utf-8") as source:
                        content = await source.read()

            except OSError as exc:
                logger.error("Failed to read file %s: %s", file_path, exc)
                return

            loop = asyncio.get_event_loop()
            try:
                # Keep processed_content: it matches node positions after ID injection.
                with tracker.timer("body_parser.scan_ast"):
                    nodes, processed_content = await loop.run_in_executor(
                        None, scan, content, str(file_path)
                    )
            except Exception as exc:
                logger.error("Failed to re-scan AST for %s: %s",
                             file_path, exc)
                return

            # Start traversal from file scope
            with tracker.timer("body_parser.traverse_ast_root"):
                await self._traverse(
                    nodes,
                    file_scope,
                    scope_map,
                    file_path=file_path,
                    source=processed_content,
                )
            self.processed_scope_ids.add(file_scope.id)

    async def _traverse(
        self,
        nodes: List[BaseNode],
        current_scope: ScopeModel,
        scope_map: dict[str, ScopeModel],
        *,
        file_path: Path,
        source: str,
    ):
        """
        Traverse AST nodes in the current scope.
        Definitions are processed sequentially (to avoid state issues).
        Calls are resolved in parallel (Jedi is the bottleneck).
        """
        call_nodes: List[CallNode] = []

        # Process definitions sequentially, collect calls
        for node in nodes:
            if isinstance(node, (ClassNode, FunctionNode)):
                if not node.id:
                    qname = f"{current_scope.qname}.{node.name}"
                    node.id = str(uuid.uuid5(uuid.NAMESPACE_URL, qname))

                child_scope = scope_map.get(node.id)
                if not child_scope:
                    continue

                if hasattr(node, "children"):
                    await self._traverse(
                        node.children, child_scope, scope_map,
                        file_path=file_path, source=source,
                    )
                self.processed_scope_ids.add(node.id)

            elif isinstance(node, CallNode):
                call_nodes.append(node)

        # Resolve ALL calls at this scope level in parallel
        if call_nodes:
            loop = asyncio.get_event_loop()

            async def _resolve(n: CallNode):
                return n, await loop.run_in_executor(
                    None,
                    self.call_chain_builder.call_resolver.resolve_call,
                    str(file_path), source, n.position.line, n.call_col_pos, None,
                )

            resolved = await asyncio.gather(*[_resolve(n) for n in call_nodes])

            for n, resolutions in resolved:
                await self.call_chain_builder.build_chain_from_resolutions(
                    call_node=n, caller_scope=current_scope,
                    resolutions=resolutions, current_call_id=None,
                    depth=0, parent_context=None,
                )

        if len(self.call_chain_builder._call_site_buffer) >= self.batch_size:
            await self.flush_all_call_sites()
