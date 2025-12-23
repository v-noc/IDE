import asyncio
from dataclasses import dataclass, field
import logging
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Set

from app.core.model.base import BaseNode
from app.core.model.nodes import CallNode
from app.core.model.properties import CodePosition
from app.core.parser.graph_builder.sync.async_helpers import AsyncSyncHelpers
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeType
from app.core.services.call_service import CallService

logger = logging.getLogger(__name__)

# Performance tracking
_timings = defaultdict(list)


@dataclass
class CallSyncBatch:
    """Batch of call infos to sync."""
    call_infos: List[dict] = field(default_factory=list)
    parent_nodes: Dict[str, object] = field(default_factory=dict)


@dataclass
class EdgeBuffers:
    """Buffers for batch edge operations."""
    contains: List[Tuple[str, str]] = field(default_factory=list)
    targets: List[Tuple[str, str]] = field(default_factory=list)


class CallSyncService:
    """Service for syncing call chains to graph database."""

    def __init__(
        self,
        scope_manager: ScopeManager,
        call_service: CallService,
        helpers: AsyncSyncHelpers,
        batch_size: int = 100,
        max_concurrent: int = 50,
    ):
        self.scope_manager = scope_manager
        self.call_service = call_service
        self.helpers = helpers
        self.batch_size = batch_size
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self.all_call_infos = []

        # Accumulated call infos from multiple files
        self._pending_call_infos: List[Tuple[dict, object]] = []

        # Stats tracking
        self._stats = defaultdict(int)

    async def collect_call_infos(self, scope_ids: List[str]) -> None:
        """
        Collect call infos from processed scopes.

        This accumulates call_infos for later batch processing.
        Equivalent to sync_call_chain_scopes but async.
        """
        for scope_id in scope_ids:
            scope = await self.scope_manager.get_scope(scope_id)
            if not scope:
                continue

            if scope.type not in (
                ScopeType.FILE,
                ScopeType.FUNCTION,
                ScopeType.CLASS,
            ):
                continue

            graph_node = await self.helpers.async_get_graph_node_for_scope(scope)
            if not graph_node:
                continue

            call_infos = await self.scope_manager.get_root_calls_from(
                scope.id, include_children=True
            )
            if call_infos:
                for call_info in call_infos:
                    self._pending_call_infos.append((call_info, graph_node))

        if len(self._pending_call_infos) > self.batch_size * 2:
            await self.batch_sync_calls()

    async def batch_sync_calls(self):
        # Track batch sync database operations
        batch_sync_start = time.time()
        print(
            f"Batch syncing {len(self.all_call_infos)} call infos")

        if not self._pending_call_infos:
            return

        queue = list(self._pending_call_infos)
        self._pending_call_infos = []

        processed_pairs: Set[Tuple[str, str]] = set()

        while queue:
            batch = queue[:self.batch_size]
            queue = queue[self.batch_size:]

            edge_buffers = EdgeBuffers()
            recursive_calls = await self._process_batch(
                batch, processed_pairs, edge_buffers
            )

            await self._flush_edges(edge_buffers)

            queue.extend(recursive_calls)

        batch_sync_time = time.time() - batch_sync_start
        _timings["batch_sync_calls_total"].append(batch_sync_time)

    async def _process_batch(
        self,
        batch: List[Tuple[dict, object]],
        processed_pairs: Set[Tuple[str, str]],
        edge_buffers: EdgeBuffers,
    ) -> List[Tuple[dict, object]]:
        """
        Process a batch of call infos.
        """
        lookup_pairs = []
        pair_to_items: Dict[Tuple[str, str],
                            List[Tuple[dict, object, object]]] = defaultdict(list)

        for call_info, parent_node in batch:
            call_site = call_info.get("call_site")
            callee_scope = call_info.get("callee")

            if not call_site or not callee_scope:
                continue

            process_key = (parent_node.id, call_site.id)
            if process_key in processed_pairs:
                continue
            processed_pairs.add(process_key)

            callee_node = await self.helpers.async_get_graph_node_for_scope(callee_scope)
            if not callee_node:
                continue

            pair = (parent_node.id, callee_node.id)
            if pair not in pair_to_items:
                lookup_pairs.append(pair)
            pair_to_items[pair].append((call_info, parent_node, callee_node))

        if not lookup_pairs:
            return []

        call_repo = self.call_service.repos.call_repo
        existing_calls = await call_repo.find_calls_by_target_parent_batch(
            lookup_pairs
        )

        recursion_counts = await call_repo.count_recursive_calls_upward_batch(lookup_pairs)
        recursive_calls = []

        for pair in lookup_pairs:
            items = pair_to_items[pair]
            call_node = existing_calls.get(pair)

            for call_info, parent_node, callee_node in items:
                # Skip deeply recursive calls
                recursion_count = recursion_counts.get(pair, 0)
                if recursion_count >= 2:
                    logger.debug(
                        f"Skipping recursive: {pair} (depth: {recursion_count})")
                    continue

                # Sync call node
                call_node = await self._sync_call_node(
                    call_info, parent_node, callee_node, call_node, edge_buffers
                )

                # Queue recursive calls
                if call_node:
                    call_site_id = call_info.get("call_site").id
                    recursive_calls.append((call_site_id, call_node))

        # Phase 5: Batch fetch recursive call targets
        if recursive_calls:
            recursive_infos = await self._fetch_recursive_calls(recursive_calls)
            return recursive_infos

        return []

    async def _sync_call_node(
        self,
        call_info: dict,
        parent_node,
        callee_node,
        existing_call_node: Optional[CallNode],
        edge_buffers: EdgeBuffers,
    ) -> Optional[CallNode]:
        """
        Sync a single call node.
        """

        call_site = call_info.get("call_site")
        callee_scope = call_info.get("callee")

        if not call_site or not callee_scope:
            return call_node

        call_node = existing_call_node

        if not call_node:
            try:
                parent_qname = parent_node.qname
                if parent_node.node_type == "call":
                    target_node = await self.helpers.async_get_call_target(parent_node.id)
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
                )

                call_node = await self.call_service.repos.call_repo.create(call_node)
                self._stats['calls_created'] += 1
            except Exception as e:
                logger.error(f"Error creating call node: {e}")
                from traceback import format_exc
                print(format_exc())
                return None
        else:
            # Update existing - nothing to update without version
            self._stats['calls_updated'] += 1

        # Add edges to buffer
        edge_buffers.contains.append((parent_node.id, call_node.id))
        edge_buffers.targets.append((call_node.id, callee_node.id))

        return call_node

    async def _fetch_recursive_calls(
        self,
        call_site_node_pairs: List[Tuple[str, object]],
    ) -> List[Tuple[dict, object]]:
        """
        Batch fetch calls inside callee scopes for recursion.
        """
        call_site_ids = [cid for cid, _ in call_site_node_pairs]

        calls_map = await self.scope_manager.batch_get_calls_inside_callee(
            call_site_ids)

        results = []
        for call_site_id, call_node in call_site_node_pairs:
            callee_call_infos = calls_map.get(call_site_id, [])
            for callee_call_info in callee_call_infos:
                results.append((callee_call_info, call_node))

        return results

    async def _flush_edges(self, edge_buffers: EdgeBuffers) -> None:
        """Batch flush edge buffers to database."""
        async with self._semaphore:
            # Concurrent edge creation
            await asyncio.gather(
                self.helpers.async_ensure_contains_edges_batch(
                    edge_buffers.contains),
                self.helpers.async_ensure_targets_edges_batch(
                    edge_buffers.targets),
            )

    def get_stats(self) -> Dict[str, int]:
        """Get sync statistics."""
        return dict(self._stats)
