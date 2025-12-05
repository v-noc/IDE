import logging
import time
from collections import defaultdict
from typing import Optional

from app.core.model.nodes import CallNode
from app.core.model.properties import CodePosition
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeType
from app.core.services.call_service import CallService
from app.core.model.base import BaseNode
from app.core.parser.graph_builder.sync.sync_helpers import SyncHelpers

logger = logging.getLogger(__name__)

# Performance tracking
_timings = defaultdict(list)


class CallSyncService:
    """Service for syncing call chains to graph database."""

    def __init__(
        self,
        scope_manager: ScopeManager,
        call_service: CallService,
        helpers: SyncHelpers,
    ):
        self.scope_manager = scope_manager
        self.call_service = call_service
        self.helpers = helpers

    def sync_call_chains(self, root_scope_id: str):
        """
        Sync call chains AFTER scopes are fully synced and
        call sites have been registered in the scope manager.

        This creates/updates CallNode documents and ensures
        targets and contains edges with the version.

        Args:
            root_scope_id: The root scope ID to start from
        """
        global _timings
        _timings.clear()

        logger.info(
            "Syncing call chains from %s with version %s",
            root_scope_id,
            self.helpers.sync_version,
        )

        root_scope = self.scope_manager.get_scope(root_scope_id)
        if not root_scope:
            logger.error(
                "Root scope %s not found for call sync", root_scope_id
            )
            return

        # Collect all call infos first, then batch process
        all_call_infos = []
        scope_to_node_map = {}

        # Simple DFS over scope tree rooted at root_scope
        stack = [root_scope]
        while stack:
            scope = stack.pop()

            if scope.type in (
                ScopeType.FILE,
                ScopeType.FUNCTION,
                ScopeType.CLASS,
            ):
                t0 = time.time()
                graph_node = self.helpers.get_graph_node_for_scope(scope)
                _timings['get_graph_node_for_scope'].append(
                    time.time() - t0
                )

                if graph_node:
                    scope_to_node_map[scope.id] = graph_node

                    t0 = time.time()
                    call_infos = self.scope_manager.get_calls_from(scope.id)
                    _timings['get_calls_from'].append(time.time() - t0)

                    for call_info in call_infos:
                        all_call_infos.append((call_info, graph_node))

            t0 = time.time()
            children = self.scope_manager.get_children(scope.id)
            _timings['get_children'].append(time.time() - t0)
            stack.extend(children)

        # Batch process calls
        self._batch_sync_calls(all_call_infos, scope_to_node_map)

        # Print timing summary
        self._print_timing_summary()

    def _batch_sync_calls(
        self,
        all_call_infos: list,
        scope_to_node_map: dict,
    ):
        """
        Batch sync calls to reduce database round trips.
        Processes calls iteratively, collecting recursive calls for next batch.

        Dedup: Within the same parent, siblings with same target are merged.
        Across different parents, the same call_site can create separate CallNodes.
        """
        # Queue of call infos to process
        queue = list(all_call_infos)
        # Track (parent_id, call_site_id) to allow same call_site under different parents
        processed_pairs = set()

        while queue:
            # Collect batch of (parent_id, target_id) pairs
            batch_pairs = []
            call_info_map = {}
            batch_size = min(500, len(queue))

            for _ in range(batch_size):
                if not queue:
                    break

                call_info, parent_node = queue.pop(0)
                call_site = call_info.get("call_site")
                callee_scope = call_info.get("callee")

                if not call_site or not callee_scope:
                    continue

                # Skip if this (parent, call_site) was already processed
                process_key = (parent_node.id, call_site.id)
                if process_key in processed_pairs:
                    continue

                # Resolve callee node
                callee_node = (
                    self.helpers.get_graph_node_for_scope(callee_scope)
                )
                if not callee_node:
                    continue

                pair = (parent_node.id, callee_node.id)
                if pair not in call_info_map:
                    call_info_map[pair] = []
                    batch_pairs.append(pair)
                call_info_map[pair].append(
                    (call_info, parent_node, callee_node, process_key)
                )

            # Batch lookup existing call nodes
            if batch_pairs:
                t0 = time.time()
                call_repo = self.call_service.repos.call_repo
                existing_calls = (
                    call_repo.find_calls_by_target_parent_batch(batch_pairs)
                )
                _timings['get_call_with_parent_and_target_batch'].append(
                    time.time() - t0
                )

                # Process each pair - track call_node across iterations
                for pair in batch_pairs:
                    call_node = existing_calls.get(pair)
                    
                    for call_info, parent_node, callee_node, process_key in call_info_map[pair]:
                        # Sync and get back the (possibly created) call_node
                        call_node, recursive = self._sync_node_calls_with_node(
                            call_info, parent_node, callee_node, call_node
                        )
                        
                        processed_pairs.add(process_key)

                        # Add recursive calls to queue
                        if recursive:
                            for nested_call_info, nested_parent in recursive:
                                nested_call_site = nested_call_info.get("call_site")
                                if nested_call_site and nested_parent:
                                    nested_key = (nested_parent.id, nested_call_site.id)
                                    if nested_key not in processed_pairs:
                                        queue.append((nested_call_info, nested_parent))

    def _sync_node_calls(
        self, call_info: dict, parent_node: BaseNode
    ):
        """
        Sync calls from a scope (calls that originated in this scope).
        This method resolves callee and looks up call node individually.
        """
        call_site = call_info.get("call_site")
        callee_scope = call_info.get("callee")

        if not call_site or not callee_scope:
            return

        # Resolve callee node in the main graph
        t0 = time.time()
        callee_node = self.helpers.get_graph_node_for_scope(callee_scope)
        _timings['get_graph_node_for_scope_callee'].append(
            time.time() - t0
        )
        if not callee_node:
            return

        # Find existing CallNode by (parent container, target)
        t0 = time.time()
        call_node = self.call_service.get_call_with_parent_and_target(
            parent_id=parent_node.id,
            target_id=callee_node.id,
        )
        _timings['get_call_with_parent_and_target'].append(
            time.time() - t0
        )

        self._sync_node_calls_with_node(
            call_info, parent_node, callee_node, call_node
        )

    def _sync_node_calls_with_node(
        self,
        call_info: dict,
        parent_node: BaseNode,
        callee_node: BaseNode,
        call_node: Optional[CallNode],
    ) -> tuple[Optional[CallNode], list]:
        """
        Sync calls from a scope (calls that originated in this scope).

        Args:
            call_info: Dictionary with 'call_site' and 'callee' keys
            parent_node: The parent node (file/function/class)
            callee_node: The callee node (already resolved)
            call_node: Existing call node (if found) or None

        Returns:
            Tuple of (call_node, recursive_calls). call_node is the created
            or existing CallNode (for reuse across multiple call sites with
            the same parent/target pair).
        """
        try:
            call_site = call_info.get("call_site")
            callee_scope = call_info.get("callee")

            # We only care about resolved calls (have a callee scope)
            if not call_site or not callee_scope:
                return call_node, []

            # If no CallNode exists yet, this is a new call site → create it
            if not call_node:
                try:
                    parent_qname = parent_node.qname
                    if parent_node.node_type == "call":
                        # For call nodes, get the target via edges
                        t0 = time.time()
                        target_node = (
                            self.helpers.repos.call_repo.get_target(
                                parent_node.id
                            )
                        )
                        _timings['get_target'].append(time.time() - t0)
                        if target_node:
                            parent_qname = target_node.qname
                    call_node = CallNode(
                        name=call_site.name or "call",
                        qname=f"{parent_qname}::{callee_scope.qname}",
                        description=f"Call: {call_site.name}",
                        position=CodePosition(
                            line_no=call_site.line,
                            col_offset=call_site.col,
                            end_line_no=call_site.line,
                            end_col_offset=call_site.col,
                        ),
                        current_version=self.helpers.sync_version,
                    )
                    t0 = time.time()
                    call_node = self.helpers.repos.call_repo.create(call_node)
                    _timings['create_call_node'].append(time.time() - t0)
                except Exception as e:
                    logger.error(
                        "Error creating call node for %s at %s:%s: %s",
                        call_site.name,
                        call_site.line,
                        call_site.col,
                        e,
                    )
                    return call_node, []

            # Update call node version only (CallNode is the call site)
            try:
                if call_node.current_version != self.helpers.sync_version:
                    call_node.current_version = self.helpers.sync_version
                    t0 = time.time()
                    self.helpers.repos.call_repo.update(
                        call_node.key, call_node
                    )
                    _timings['update_call_node'].append(time.time() - t0)
            except Exception as e:
                logger.error(
                    "Error updating call node %s version: %s",
                    call_node.id,
                    e,
                )
                return call_node, []

            # Ensure contains edge from parent container -> call
            t0 = time.time()
            self.helpers.ensure_contains_edge(
                parent_node.id,
                call_node.id,
                self.helpers.sync_version
            )
            _timings['ensure_contains_edge'].append(time.time() - t0)

            # Ensure / update targets edge call -> callee
            t0 = time.time()
            self.helpers.ensure_targets_edge(call_node.id, callee_node.id)
            _timings['ensure_targets_edge'].append(time.time() - t0)

            # Collect recursive calls instead of processing immediately
            recursive_calls = []

            # Recursively sync calls inside the callee scope.
            # Get calls made INSIDE the callee function/class.
            t0 = time.time()
            callee_call_infos = self.scope_manager.get_calls_inside_callee(
                call_site.id
            )
            _timings['get_calls_inside_callee'].append(time.time() - t0)

            for callee_call_info in callee_call_infos:
                recursive_calls.append((callee_call_info, call_node))

            # Also sync NEXT_IN_CHAIN call sites (method chaining)
            t0 = time.time()
            chain_children = self.scope_manager.get_call_chain_children(
                call_site.id
            )
            _timings['get_call_chain_children'].append(time.time() - t0)

            for chain_child_info in chain_children:
                recursive_calls.append((chain_child_info, call_node))

            return call_node, recursive_calls

        except Exception as e:
            logger.error(
                f"Error syncing call node: {e}"
            )
            return call_node, []

    def _print_timing_summary(self):
        """Print timing statistics for performance analysis."""
        global _timings
        from app.core.parser.graph_builder.sync.sync_helpers import (
            _timings as helper_timings
        )

        # Merge timings from sync_helpers
        all_timings = dict(_timings)
        for key, value in helper_timings.items():
            if key not in all_timings:
                all_timings[key] = value
            else:
                all_timings[key].extend(value)

        if not all_timings:
            return

        print("\n" + "=" * 80)
        print("CALL SYNC PERFORMANCE TIMING SUMMARY")
        print("=" * 80)

        total_time = 0.0
        for operation, times in sorted(all_timings.items()):
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
