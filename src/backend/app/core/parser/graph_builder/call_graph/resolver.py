import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.model.nodes import CodePosition
from app.core.parser.ast.models import CallNode as ASTCallNode
from app.core.parser.jedi_adapter.call_resolver import CallResolver as JediAdapter
from app.core.parser.jedi_adapter.manager import JediProjectManager
from app.core.repository import Repositories
from app.core.parser.graph_builder.performance import tracker

from .models import ResolvedCall
from app.core.model.schemas.code_element_schema import FunctionSchema

logger = logging.getLogger(__name__)


class CallResolverService:
    def __init__(self, jedi_manager: JediProjectManager, repos: Repositories):
        self.jedi_manager = jedi_manager
        self.repos = repos
        self.adapter = JediAdapter(jedi_manager)
        self.semaphore = asyncio.Semaphore(1)

    async def resolve_scope_calls(
        self,
        file_path: Path,
        source_code: str,
        ast_calls: List[ASTCallNode],
        parent_context: Optional[Any] = None,
    ) -> Tuple[List[ResolvedCall], Dict[str, List[Any]]]:
        """
        Resolves a batch of AST call nodes to DB IDs in parallel.
        Returns a list of ResolvedCall objects.
        """
        if not ast_calls:
            return [], {}

        loop = asyncio.get_event_loop()

        async def resolve_with_semaphore(ast_node: ASTCallNode):
            async with self.semaphore:
                return await loop.run_in_executor(
                    None,
                    self.adapter.resolve_call,
                    str(file_path),
                    source_code,
                    ast_node.position.line,
                    ast_node.call_col_pos,
                    parent_context,
                )

        # Prepare parallel resolution tasks
        tasks = [resolve_with_semaphore(ast_node) for ast_node in ast_calls]

        # 1. Resolve to Jedi Definitions
        with tracker.timer("call_graph.resolve_jedi_calls"):
            jedi_results = await asyncio.gather(*tasks, return_exceptions=True)

        resolved_calls_map: Dict[str, ResolvedCall] = {}
        context_map: Dict[str, List[Any]] = {}

        with tracker.timer("call_graph.process_resolved_calls"):
            for i, resolutions in enumerate(jedi_results):
                if isinstance(resolutions, Exception) or not resolutions:
                    if isinstance(resolutions, Exception):
                        print(f"Error resolving call: {resolutions}")
                    else:
                        print(
                            f"\n\nNo resolutions found for call: {ast_calls[i]} has parent context -{parent_context == None}")
                    continue

                # We iterate all resolutions to capture all contexts
                for resolution in resolutions:
                    target_id = getattr(resolution, "callee_id", None)
                    target_qname = getattr(
                        resolution, "callee_qname", "unknown")

                    if not target_id:
                        continue

                    db_target_id = f"{FunctionSchema.__name__}/{target_id}"

                    # 1. Collect Contexts (Do not skip if target_id exists!)
                    if db_target_id not in context_map:
                        context_map[db_target_id] = []

                    next_context = getattr(
                        resolution, "execution_context", None)
                    if next_context:
                        context_map[db_target_id].append(next_context)

                    # 2. Keep only one ResolvedCall object per target for the Processor
                    # We use the first occurrence to define the edge properties (like position)
                    if db_target_id not in resolved_calls_map:
                        ast_node = ast_calls[i]
                        resolved_calls_map[db_target_id] = ResolvedCall(
                            target_id=db_target_id,
                            target_qname=target_qname,
                            call_node_name=ast_node.name or "call",
                            position=CodePosition(
                                line_no=ast_node.position.line,
                                col_offset=ast_node.position.column,
                                end_line_no=ast_node.position.end_line,
                                end_col_offset=ast_node.position.end_column,
                            ),
                        )

        return list(resolved_calls_map.values()), context_map
