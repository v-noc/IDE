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
from typing import List, Optional, Dict

from app.core.parser.ast.models import (
    BaseNode,
    CallNode,
    ClassNode,
    FunctionNode,
)
from app.core.parser.ast.scanner import scan
from app.core.parser.jedi_adapter.call_resolver import CallResolver
from app.core.parser.jedi_adapter.manager import JediProjectManager
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeModel

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
        scope_manager: ScopeManager,
        jedi_manager: JediProjectManager,
        max_depth: int = 1,
    ):
        self.project_path = project_path
        self.project_name = project_name
        self.scope_manager = scope_manager
        self.jedi_manager = jedi_manager
        self.call_resolver = CallResolver(jedi_manager)
        self.max_depth = max_depth

        # for recursive detection
        self.call_chain_scope_ids: Dict[str, int] = {}

        # Batch processing for call sites
        self._call_site_buffer: List[dict] = []
        # Maps temp_id -> actual_id for resolved call sites
        self._temp_id_to_actual_id: dict = {}

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

    async def _get_scope_with_retry(
        self,
        scope_id: Optional[str] = None,
        qname: Optional[str] = None,
        max_retries: int = 1,
        initial_delay: float = 0.01,
    ) -> Optional[ScopeModel]:
        """
        Get a scope with retry logic to handle race conditions.

        When scopes are created in parallel threads, there can be a race
        condition where one thread tries to fetch a scope before it's fully
        committed to the database. This method retries with exponential
        backoff.

        Args:
            scope_id: Scope ID to fetch (priority 1)
            qname: Qualified name to fetch (priority 2, if scope_id fails)
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before retry

        Returns:
            ScopeModel if found, None otherwise
        """
        delay = initial_delay
        scope = None

        for attempt in range(max_retries):
            # Try ID-based lookup first
            if scope_id:
                scope = await self.scope_manager.get_scope(scope_id)
                if scope:
                    return scope

            # Try qname-based lookup if ID failed or wasn't provided
            if qname:
                print(f"Getting scope by qname: {qname} {scope_id}")
                scope = await self.scope_manager.get_scope_by_qname(qname)
                if scope:
                    return scope

            # If not found and we have retries left, wait and retry
            # if attempt < max_retries - 1:
            #     print(f"Waiting {delay} seconds to retry")
            #     print(f"Attempt {attempt} of {max_retries}")
            #     time.sleep(delay)
            #     delay *= 2  # Exponential backoff

        return None

    async def build_chain(
        self,
        call_node: CallNode,
        caller_scope: ScopeModel,
        current_call_id: Optional[str] = None,
        depth: int = 2,
        parent_context: Optional[object] = None,
    ) -> Optional[str]:
        """
        Build a call chain starting from a call node.

        This method:
        1. Uses Jedi to resolve the call WITH context preservation
        2. Creates a call site linking caller -> callee
        3. Returns the call site ID for chaining

        Note: Does NOT recursively process callee bodies - BodyParser
              handles that during its traversal of the AST.

        Args:
            call_node: The AST CallNode to resolve
            caller_scope: The scope containing this call
            current_call_id: ID of the previous call site in the chain
            depth: Current recursion depth (unused, kept for compatibility)
            parent_context: Optional Jedi context from the caller

        Returns:
            The ID of the created call site
        """
        # If we are at the top level, clear the call chain scope ids
        if parent_context is None:

            self.call_chain_scope_ids.clear()

        file_path = Path(caller_scope.file_path)
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
        resolutions = await loop.run_in_executor(None, self.call_resolver.resolve_call,
                                                 str(file_path),
                                                 source,
                                                 call_node.position.line,
                                                 call_node.call_col_pos,
                                                 parent_context,
                                                 )
        resolve_time = time.time() - t0
        _timings["resolve_call"].append(resolve_time)
        # Track instance-level stats
        self._instance_stats["resolve_call_count"] += 1
        self._instance_stats["resolve_call_time"] += resolve_time
        if not resolutions:
            logger.debug(
                f"Could not resolve call {call_node.name} at "
                f"{call_node.position.line}:{call_node.position.column}"
            )
            return None

        call_site_ids = []
        call_name = self._normalize_call_name(call_node.name)
        call_line = call_node.position.line
        call_col = call_node.call_col_pos

        # Process each resolution separately
        for resolution in resolutions:
            # Determine callee_id based on resolution
            # Use retry logic to handle race conditions with concurrent
            # scope creation
            t0 = time.time()
            callee_scope = await self._get_scope_with_retry(
                scope_id=resolution.callee_id,
                qname=resolution.qname,
            )
            get_scope_time = time.time() - t0
            _timings["get_scope_with_retry"].append(get_scope_time)
            # Track instance-level stats
            self._instance_stats["get_scope_count"] += 1
            self._instance_stats["get_scope_time"] += get_scope_time

            # If still not found, log and skip this resolution
            if not callee_scope:
                print(
                    f"Could not resolve call {resolution} "
                    f"{call_node.name} at "
                    f"{call_node.position.line}:"
                    f"{call_node.position.column} "
                    f"(callee_id={resolution.callee_id}, "
                    f"qname={resolution.qname})"
                )
                continue

            if callee_scope.id not in self.call_chain_scope_ids:
                self.call_chain_scope_ids[callee_scope.id] = 0
            else:
                self.call_chain_scope_ids[callee_scope.id] += 1

            if self.call_chain_scope_ids[callee_scope.id] >= self.max_depth:
                continue

            # Generate call site ID (will be created in batch)
            import uuid

            call_site_id = str(uuid.uuid4())

            # Add to batch buffer instead of creating immediately
            self._call_site_buffer.append(
                {
                    "caller_id": caller_scope.id,
                    "line": call_line,
                    "col": call_col,
                    "name": call_name,
                    "callee_id": callee_scope.id,
                    "prev_call_site_id": current_call_id,
                    "_temp_id": call_site_id,  # Temporary ID for chaining
                }
            )

            # Extract execution context for recursion
            execution_context = getattr(resolution, 'execution_context', None)

            # Process each body separately
            await self._process_scope_body(
                callee_scope, depth + 1, call_site_id, execution_context
            )

            call_site_ids.append(call_site_id)

        return call_site_ids if call_site_ids else None

    def _candidate_qnames(
        self,
        caller_scope: ScopeModel,
        jedi_qname: str,
    ) -> List[str]:
        """
        Generate possible fully-qualified qnames for a callee based on the
        caller scope.

        Jedi often returns module-relative names. This method tries:
        1. The raw qname (if already project-qualified)
        2. Project + module + qname (same file/module reference)
        3. Project + qname (cross-module references within the project)
        """
        if not jedi_qname:
            return []

        normalized = jedi_qname.strip().strip(".")
        if not normalized:
            return []

        project_prefix = self.project_name

        candidates: List[str] = []

        if normalized.startswith(f"{project_prefix}."):
            candidates.append(normalized)

        candidates.append(f"{project_prefix}.{normalized}")

        # Deduplicate while preserving order
        seen = set()
        ordered = []
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                ordered.append(candidate)
        return ordered

    def _normalize_call_name(self, raw_name: Optional[str]) -> Optional[str]:
        """
        Normalize the call site name for comparisons (use last attribute
        segment).
        """
        if not raw_name:
            return raw_name

        segment = raw_name.strip().split(".")[-1]
        if segment.endswith("()"):
            segment = segment[:-2]

        segment = segment.strip()
        return segment or raw_name

    async def _process_scope_body(
        self,
        scope: ScopeModel,
        depth: int,
        current_call_id,
        parent_context: Optional[object] = None,
    ):
        """
        Process all calls within a function/method scope.

        Args:
            scope: The scope to process
            depth: Current recursion depth
            current_call_id: ID of the previous call
            parent_context: Optional Jedi context to use for resolution
                within this body
        """
        logger.debug(f"Processing body of {scope.qname}")

        # Get the source code
        file_path = Path(scope.file_path)
        if not file_path.is_absolute():
            file_path = self.project_path / file_path

        t0 = time.time()
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                source = await f.read()
        except OSError as e:
            logger.error(f"Could not read file {file_path}: {e}")
            return
        _timings["read_file_body"].append(time.time() - t0)

        # Parse the AST
        t0 = time.time()
        loop = asyncio.get_event_loop()
        try:
            nodes = await loop.run_in_executor(None, scan, source, str(file_path))
        except Exception as e:
            logger.error(f"Failed to scan AST for {file_path}: {e}")
            return
        _timings["scan_ast"].append(time.time() - t0)

        # Find the function/class node that corresponds to this scope
        t0 = time.time()
        target_node = self._find_scope_node(nodes, scope)
        _timings["find_scope_node"].append(time.time() - t0)

        if not target_node:
            logger.warning(f"Could not find AST node for scope {scope.qname}")
            return

        # Extract all call nodes from this scope's body
        t0 = time.time()
        call_nodes = self._extract_calls(target_node)
        _timings["extract_calls"].append(time.time() - t0)

        logger.debug(f"Found {len(call_nodes)} call(s) in {scope.qname}")

        for call_node in call_nodes:
            await self.build_chain(
                call_node,
                scope,
                current_call_id,  # Pass through the parent call site ID for chaining
                depth,
                parent_context=parent_context,
            )

    def _find_scope_node(
        self, nodes: List[BaseNode], scope: ScopeModel
    ) -> Optional[BaseNode]:
        """
        Find the AST node that corresponds to a scope.

        Matches based on qname or position.
        """
        for node in nodes:
            # Check if this node matches the scope
            if isinstance(node, (FunctionNode, ClassNode)):
                # Match by position (line)
                if node.position.line == scope.start_line and node.name == scope.name:
                    return node

            # Recurse into children
            if hasattr(node, "children"):
                result = self._find_scope_node(node.children, scope)
                if result:
                    return result

        return None

    def _extract_calls(self, node: BaseNode) -> List[CallNode]:
        """
        Extract all CallNode instances from a node's children.

        Only extracts direct calls, not calls nested in child scopes.
        """
        calls = []

        if hasattr(node, "children"):
            for child in node.children:
                if isinstance(child, CallNode):
                    calls.append(child)
                elif isinstance(child, (FunctionNode, ClassNode)):
                    # Don't recurse into nested scopes
                    continue
                else:
                    # Recurse into other nodes (If, For, etc.)
                    calls.extend(self._extract_calls(child))

        return calls

    async def _flush_all_buffered_call_sites(self) -> None:
        """
        Flush all call sites in the buffer.

        This is called per file to batch all call sites from all scopes
        in that file together for maximum performance.
        """
        if not self._call_site_buffer:
            return

        # Collect temp IDs in this batch
        batch_temp_ids = {
            item.get("_temp_id")
            for item in self._call_site_buffer
            if item.get("_temp_id")
        }

        # Resolve prev_call_site_id references:
        # - If it's a temp ID from a previous batch, resolve it
        # - If it's a temp ID from this batch, we'll handle it after creation
        # - Otherwise, it's already an actual ID
        deferred_chain_links = []  # Store (temp_prev_id, temp_curr_id) pairs

        for item in self._call_site_buffer:
            prev_id = item.get("prev_call_site_id")
            temp_id = item.get("_temp_id")

            if prev_id:
                if prev_id in self._temp_id_to_actual_id:
                    # Resolve from previous batch (from previous file)
                    item["prev_call_site_id"] = self._temp_id_to_actual_id[prev_id]
                elif prev_id in batch_temp_ids:
                    # Defer: this is a temp ID in the same batch
                    deferred_chain_links.append((prev_id, temp_id))
                    item["prev_call_site_id"] = (
                        None  # Remove for now, add relationship later
                    )

        # Prepare batch data (without _temp_id and with resolved prev_call_site_id)
        batch_data = []
        for item in self._call_site_buffer:
            batch_data.append(
                {
                    "caller_id": item["caller_id"],
                    "line": item["line"],
                    "col": item["col"],
                    "name": item.get("name"),
                    "callee_id": item.get("callee_id"),
                    "prev_call_site_id": item.get("prev_call_site_id"),
                }
            )

        # Batch create call sites
        t0 = time.time()
        created_call_sites = await self.scope_manager.batch_create_calls(batch_data)
        _timings["create_call_site"].append(time.time() - t0)

        # Map temp IDs from this batch to actual IDs
        for i, item in enumerate(self._call_site_buffer):
            temp_id = item.get("_temp_id")
            if temp_id and i < len(created_call_sites):
                actual_id = created_call_sites[i].id
                self._temp_id_to_actual_id[temp_id] = actual_id

        # Create deferred NEXT_IN_CHAIN relationships
        # if deferred_chain_links:
        #     from app.core.parser.scope_manager.repository import ScopeRepository

        #     repo: ScopeRepository = self.scope_manager.repository

        #     chain_data = []
        #     for prev_temp_id, curr_temp_id in deferred_chain_links:
        #         prev_actual_id = self._temp_id_to_actual_id.get(prev_temp_id)
        #         curr_actual_id = self._temp_id_to_actual_id.get(curr_temp_id)
        #         if prev_actual_id and curr_actual_id:
        #             chain_data.append(
        #                 {
        #                     "prev_id": prev_actual_id,
        #                     "curr_id": curr_actual_id,
        #                 }
        #             )

        #     if chain_data:
        #         async with self.scope_manager.semaphore:
        #             await repo.conn.execute(
        #                 """
        #                 UNWIND $chains AS c
        #                 MATCH (prev:CallSite {id: c.prev_id})
        #                 MATCH (curr:CallSite {id: c.curr_id})
        #                 CREATE (prev)-[:NEXT_IN_CHAIN]->(curr)
        #                 """,
        #                 {"chains": chain_data},
        #             )

        logger.debug(
            f"Flushed {len(self._call_site_buffer)} call site(s) for file")

        # Clear the buffer
        self._call_site_buffer.clear()

    async def flush_all_call_sites(self) -> None:
        """Flush all remaining call sites in the buffer."""
        await self._flush_all_buffered_call_sites()
        self.reset_visited()

    def reset_visited(self):
        """Reset the visited scopes tracker."""

        self._call_site_buffer.clear()
        self._temp_id_to_actual_id.clear()

    def get_stats(self) -> dict:
        """Get instance-level statistics."""
        return self._instance_stats.copy()

    def print_timing_summary(self):
        """Print timing statistics for performance analysis."""
        global _timings

        if not _timings:
            return

        print("\n" + "=" * 80)
        print("CALL CHAIN BUILDER PERFORMANCE TIMING SUMMARY")
        print("=" * 80)

        total_time = 0.0
        for operation, times in sorted(_timings.items()):
            if times:
                count = len(times)
                total = sum(times)
                avg = total / count
                max_time = max(times)
                min_time = min(times)
                total_time += total

                print(
                    f"{operation:40s} "
                    f"count: {count:6d} "
                    f"total: {total:8.4f}s "
                    f"avg: {avg:8.6f}s "
                    f"max: {max_time:8.6f}s "
                    f"min: {min_time:8.6f}s"
                )

        print("=" * 80)
        print(f"TOTAL TIME IN TRACKED OPERATIONS: {total_time:.4f}s")
        print("=" * 80 + "\n")
