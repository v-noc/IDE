import asyncio
import logging
from typing import List, Optional, Set, Tuple
from pathlib import Path

from app.core.parser.ast.models import CallNode as ASTCallNode
from app.core.parser.jedi_adapter.manager import JediProjectManager
from app.core.parser.jedi_adapter.call_resolver import CallResolver as JediAdapter
from app.core.repository import Repositories
from app.core.model.nodes import CodePosition
from .models import ResolvedCall

logger = logging.getLogger(__name__)


class CallResolverService:
    def __init__(self, jedi_manager: JediProjectManager, repos: Repositories):
        self.jedi_manager = jedi_manager
        self.repos = repos
        self.adapter = JediAdapter(jedi_manager)

    async def resolve_scope_calls(
        self,
        file_path: Path,
        source_code: str,
        ast_calls: List[ASTCallNode]
    ) -> List[ResolvedCall]:
        """
        Resolves a batch of AST call nodes to DB IDs in parallel.
        Returns a list of ResolvedCall objects.
        """
        if not ast_calls:
            return []

        loop = asyncio.get_event_loop()
        tasks = []

        # Prepare parallel resolution tasks
        for ast_node in ast_calls:
            tasks.append(
                loop.run_in_executor(
                    None,
                    self.adapter.resolve_call,
                    str(file_path),
                    source_code,
                    ast_node.position.line,
                    ast_node.call_col_pos,
                    None
                )
            )

        # 1. Resolve to Jedi Definitions
        jedi_results = await asyncio.gather(*tasks, return_exceptions=True)

        resolved_calls: List[ResolvedCall] = []
        unique_target_check: Set[str] = set()

        for i, resolutions in enumerate(jedi_results):
            if isinstance(resolutions, Exception) or not resolutions:
                continue

            # We assume the first valid resolution is the primary target
            # (Handling overloading in Python is tricky, sticking to primary for now)
            best_resolution = resolutions[0]
            target_id = getattr(best_resolution, "callee_id", None)
            target_qname = getattr(best_resolution, "callee_qname", "unknown")

            if not target_id:
                continue

            # 2. Verify Target Exists in DB (Sanity Check)
            # We verify existence to ensure we don't link to non-existent nodes
            # Ideally this is cached or optimistic. For bulk performance,
            # we might skip this individual check if we trust the IDs.
            # Here we skip the DB check for speed, relying on ID consistency.

            # Deduplicate specifically for this list result (we handle DB dedupe later)
            if target_id in unique_target_check:
                continue

            ast_node = ast_calls[i]

            resolved_calls.append(ResolvedCall(
                target_id=f"nodes/{target_id}",
                target_qname=target_qname,
                call_node_name=ast_node.name or "call",
                position=CodePosition(
                    line_no=ast_node.position.line,
                    col_offset=ast_node.position.column,
                    end_line_no=ast_node.position.end_line,
                    end_col_offset=ast_node.position.end_column
                )
            ))
            unique_target_check.add(target_id)

        return resolved_calls
