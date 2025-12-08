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

        # First, clear CallNodes from ArangoDB for all scopes to prevent
        # duplicate edges on resync
        logger.info("Clearing old CallNodes from ArangoDB")
        scope_ids_to_clear = set()
        stack_clear = [root_scope]
        while stack_clear:
            scope = stack_clear.pop()
            if scope.type in (
                ScopeType.FILE,
                ScopeType.FUNCTION,
                ScopeType.CLASS,
            ):
                scope_ids_to_clear.add(scope.id)
            children = self.scope_manager.get_children(scope.id)
            stack_clear.extend(children)

        # Collect all call infos first, then batch process
        all_call_infos = []

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

                    t0 = time.time()
                    call_infos = self.scope_manager.get_root_calls_from(
                        scope.id, include_children=True)
                    _timings['get_calls_from'].append(time.time() - t0)

                    # Handle None or empty results
                    if call_infos:
                        for call_info in call_infos:
                            all_call_infos.append((call_info, graph_node))

                            # # Store children for later processing after
                            # # call_node is created
                            # children = call_info.get("children", [])
                            # if children:
                            #     call_site_id = call_info["call_site"].id
                            #     root_call_children[call_site_id] = children

            t0 = time.time()
            children = self.scope_manager.get_children(scope.id)
            _timings['get_children'].append(time.time() - t0)
            stack.extend(children)

        # Batch process calls
        self._batch_sync_calls(
            all_call_infos
        )

        # Print timing summary
        self._print_timing_summary()

    def _batch_sync_calls(
        self,
        all_call_infos: list,

    ):
        """
        Batch sync calls to reduce database round trips.
        Processes calls iteratively, collecting recursive calls for next batch.

        Dedup: Within the same parent, siblings with same target
        are merged. Across different parents, the same call_site
        can create separate CallNodes.
        """
        # Queue of call infos to process
        queue = list(all_call_infos)
        # Track (parent_id, call_site_id) to allow same call_site
        # under different parents
        processed_pairs = set()

        while queue:
            # Collect batch of (parent_id, target_id) pairs
            batch_pairs = []
            call_info_map = {}
            batch_size = min(500, len(queue))

            # Buffers for batch operations
            contains_edges_buffer = []  # (parent_id, child_id)
            targets_edges_buffer = []   # (call_id, callee_id)
            # (call_info, call_node) for recursive processing
            recursive_lookup_ids = []

            # 1. Process queue to build batch lookup keys

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

                processed_pairs.add(process_key)

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

                # Store item for processing after lookup
                call_info_map[pair].append(
                    (call_info, parent_node, callee_node)
                )

            # 2. Batch lookup existing call nodes
            if batch_pairs:
                t0 = time.time()
                call_repo = self.call_service.repos.call_repo
                existing_calls = (
                    call_repo.find_calls_by_target_parent_batch(batch_pairs)
                )
                _timings['get_call_with_parent_and_target_batch'].append(
                    time.time() - t0
                )

                # 3. Batch check recursion for all pairs
                recursion_check_pairs = []
                for pair in batch_pairs:
                    items = call_info_map[pair]
                    for call_info, parent_node, callee_node in items:
                        recursion_check_pairs.append(
                            (parent_node.id, callee_node.id)
                        )

                recursion_counts = {}
                if recursion_check_pairs:
                    t0 = time.time()
                    recursion_counts = (
                        call_repo.count_recursive_calls_upward_batch(
                            recursion_check_pairs
                        )
                    )
                    _timings['count_recursive_calls_upward'].append(
                        time.time() - t0
                    )

                # 4. Process each pair to create/update nodes and collect edges
                for pair in batch_pairs:
                    call_node = existing_calls.get(pair)

                    items = call_info_map[pair]
                    for call_info, parent_node, callee_node in items:
                        # Check for recursion: if target appears twice or more
                        # in upward call chain, skip to prevent infinite recursion
                        recursion_key = (
                            parent_node.id, callee_node.id
                        )
                        recursion_count = recursion_counts.get(
                            recursion_key, 0
                        )

                        if recursion_count >= 2:
                            logger.debug(
                                "Skipping recursive call: %s -> %s "
                                "(recursion depth: %d)",
                                parent_node.id,
                                callee_node.id,
                                recursion_count,
                            )
                            continue

                        # Sync and get back the (possibly created) call_node
                        call_node = self._sync_node_calls_with_node_batch(
                            call_info,
                            parent_node,
                            callee_node,
                            call_node,
                            contains_edges_buffer,
                            targets_edges_buffer
                        )

                        # Add to recursive lookup list
                        if call_node:
                            call_site_id = call_info.get("call_site").id
                            recursive_lookup_ids.append(
                                (call_site_id, call_node))

            # 4. Flush edge buffers
            if contains_edges_buffer:
                self.helpers.ensure_contains_edges_batch(contains_edges_buffer)

            if targets_edges_buffer:
                self.helpers.ensure_targets_edges_batch(targets_edges_buffer)

            # 5. Batch lookup recursive calls
            if recursive_lookup_ids:
                self._process_recursive_calls_batch(
                    recursive_lookup_ids, queue)

    def _sync_node_calls_with_node_batch(
        self,
        call_info: dict,
        parent_node: BaseNode,
        callee_node: BaseNode,
        call_node: Optional[CallNode],
        contains_edges_buffer: list,
        targets_edges_buffer: list,
    ) -> Optional[CallNode]:
        """
        Sync calls from a scope (calls that originated in this scope).
        Collects edges into buffers instead of executing immediately.
        """
        try:
            call_site = call_info.get("call_site")
            callee_scope = call_info.get("callee")

            # We only care about resolved calls (have a callee scope)
            if not call_site or not callee_scope:
                return call_node

            # If no CallNode exists yet, this is a new call site → create it
            if not call_node:
                try:
                    parent_qname = parent_node.qname
                    if parent_node.node_type == "call":
                        # For call nodes, get the target via edges
                        # Note: This is still a single lookup, could be
                        # optimized but rare for new nodes
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
                    return call_node

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
                return call_node

            # Add edges to buffer
            contains_edges_buffer.append((parent_node.id, call_node.id))
            targets_edges_buffer.append((call_node.id, callee_node.id))

            return call_node

        except Exception as e:
            logger.error(
                f"Error syncing call node: {e}"
            )
            return call_node

    def _process_recursive_calls_batch(
        self, recursive_lookup_ids: list, queue: list
    ):
        """
        Batch lookup recursive calls and add to queue.
        recursive_lookup_ids is list of (call_site_id, call_node)
        """
        if not recursive_lookup_ids:
            return

        call_site_ids = [cid for cid, _ in recursive_lookup_ids]

        # Batch fetch all calls inside callees in one query
        t0 = time.time()
        calls_map = (
            self.scope_manager.batch_get_calls_inside_callee(call_site_ids)
        )
        _timings['get_calls_inside_callee'].append(time.time() - t0)

        # Process results and add to queue
        for call_site_id, call_node in recursive_lookup_ids:
            callee_call_infos = calls_map.get(call_site_id, [])
            for callee_call_info in callee_call_infos:
                queue.append((callee_call_info, call_node))

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
