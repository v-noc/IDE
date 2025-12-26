"""
CallChainBuilder - Recursively constructs call graphs by resolving and
traversing function calls.

This module:
1. Resolves calls using CallResolver
2. Checks if resolved callees are local/registered functions
3. Recursively processes function bodies to build complete call chains
4. Handles class instantiation edge case (links to class, processes
   __init__ if present)
"""
import asyncio
import aiofiles
import logging
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional, Dict, Union

from app.core.model.nodes import CallNode, ClassNode, FunctionNode, CodePosition
from app.core.parser.ast.models import (
    CallNode as ASTCallNode,
)
from app.core.parser.jedi_adapter.call_resolver import CallResolver
from app.core.parser.jedi_adapter.manager import JediProjectManager
from app.core.repository import Repositories

logger = logging.getLogger(__name__)

# Performance tracking
_timings = defaultdict(list)


class CallChainBuilder:
    """
    Builds call chains by recursively resolving and processing function calls.

    This class integrates with CallResolver to:
    - Resolve what function is being called
    - Check if it's a local (registered) function
    - Recursively process the callee's body for nested calls
    - Build a complete call graph chain
    """

    def __init__(
        self,
        project_path: Path,
        project_name: str,
        repos: Repositories,
        jedi_manager: JediProjectManager,
        max_depth: int = 5,
    ):
        self.project_path = project_path
        self.project_name = project_name
        self.repos = repos
        self.jedi_manager = jedi_manager
        self.call_resolver = CallResolver(jedi_manager)
        self.max_depth = max_depth

        # for recursive detection
        self.call_chain_scope_ids: Dict[str, int] = {}

        # Instance-level statistics tracking
        self._instance_stats = {
            "resolve_call_count": 0,
            "resolve_call_time": 0.0,
            "get_scope_count": 0,
            "get_scope_time": 0.0,
        }

        # Clear timings on initialization
        global _timings
        _timings.clear()

    async def _get_node_with_retry(
        self,
        qname: Optional[str] = None,
        max_retries: int = 1,
        initial_delay: float = 0.01,
    ) -> Optional[Union[FunctionNode, ClassNode]]:
        """
        Get a node with retry logic to handle race conditions.
        """
        if not qname:
            return None

        # Try function first, then class
        for attempt in range(max_retries):
            # Try function
            node = await self.repos.function_repo.find_one({"qname": qname})
            if node:
                return node

            # Try class
            node = await self.repos.class_repo.find_one({"qname": qname})
            if node:
                return node

            # If not found and we have retries left, wait and retry
            if attempt < max_retries - 1:
                await asyncio.sleep(initial_delay * (2 ** attempt))

        return None

    async def build_chain(
        self,
        call_node: ASTCallNode,
        caller_node: Union[FunctionNode, ClassNode],
        depth: int = 0,
        parent_context: Optional[object] = None,
    ) -> Optional[CallNode]:
        """
        Build a call chain starting from a call node.
        """
        if depth > self.max_depth:
            return None

        file_node_info = await self.repos.nodes.get_nearest_file_and_project(caller_node.id)
        file_node = file_node_info.get("file")
        if not file_node:
            logger.warning(
                f"Could not find file for caller {caller_node.qname}")
            return None

        file_path = Path(file_node["path"])
        if not file_path.is_absolute():
            file_path = self.project_path / file_path

        t0 = time.time()
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                source = await f.read()
        except OSError as e:
            logger.error(f"Could not read file {file_path}: {e}")
            return None
        _timings["read_file"].append(time.time() - t0)

        # Resolve the call using Jedi with context preservation
        t0 = time.time()
        loop = asyncio.get_event_loop()
        resolutions = await loop.run_in_executor(
            None,
            self.call_resolver.resolve_call,
            str(file_path),
            source,
            call_node.position.line,
            call_node.call_col_pos,
            parent_context,
        )
        resolve_time = time.time() - t0
        _timings["resolve_call"].append(resolve_time)
        self._instance_stats["resolve_call_count"] += 1
        self._instance_stats["resolve_call_time"] += resolve_time

        return await self.build_chain_from_resolutions(
            call_node=call_node,
            caller_node=caller_node,
            resolutions=resolutions,
            depth=depth,
            parent_context=parent_context,
        )

    async def build_chain_from_resolutions(
        self,
        *,
        call_node: ASTCallNode,
        caller_node: Union[FunctionNode, ClassNode],
        resolutions: Optional[list],
        depth: int = 0,
        parent_context: Optional[object] = None,
    ) -> Optional[CallNode]:
        """
        Build a call chain when resolutions have already been computed.
        """
        if not resolutions:
            return None

        created_call_node = None

        for resolution in resolutions:
            t0 = time.time()
            callee_qname = getattr(resolution, "qname", None)

            callee_node = await self._get_node_with_retry(
                qname=callee_qname,
            )

            get_scope_time = time.time() - t0
            _timings["get_scope_with_retry"].append(get_scope_time)
            self._instance_stats["get_scope_count"] += 1
            self._instance_stats["get_scope_time"] += get_scope_time

            if not callee_node:
                # External or unresolvable call
                continue

            # Check recursion depth
            recursion_count = await self.repos.call_repo.count_recursion_depth(
                caller_node.id, callee_node.id
            )
            if recursion_count >= 2:  # Limit recursion
                continue

            # Create CallNode
            try:
                db_call_node = CallNode(
                    name=call_node.name or "call",
                    qname=f"{caller_node.qname}::{callee_node.qname}",
                    position=CodePosition(
                        line_no=call_node.position.line,
                        col_offset=call_node.position.column,
                        end_line_no=call_node.position.end_line,
                        end_col_offset=call_node.position.end_column
                    ),
                    node_type="call"
                )

                created_node = await self.repos.call_repo.create_with_edges(
                    db_call_node,
                    parent_id=caller_node.id,
                    target_id=callee_node.id
                )
                created_call_node = created_node

            except Exception as e:
                logger.error(f"Error creating call node: {e}")
                continue

        return created_call_node

    def get_stats(self) -> dict:
        """Get instance-level statistics."""
        return self._instance_stats.copy()
