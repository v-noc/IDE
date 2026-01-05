import logging
from typing import List, Set, Optional
from .models import ResolvedCall, ScopeSyncResult
from .repository_extension import CallGraphRepository
from app.core.model.nodes import ContainerNode

logger = logging.getLogger(__name__)


class ScopeProcessor:
    def __init__(self, repo: CallGraphRepository):
        self.repo = repo

    async def sync_scope(
        self,
        parent_node: ContainerNode,
        resolved_calls: List[ResolvedCall],
        parent_call_node_id: Optional[str] = None
    ) -> ScopeSyncResult:
        """
        Synchronizes the DB for a specific parent node.
        Ensures exactly one CallNode exists per unique target_id.
        """

        parent_id = parent_node.id

        if parent_call_node_id:
            parent_id = parent_call_node_id

        created_map = {}

        # 1. Identify what currently exists in DB
        # Map: target_id -> call_node_id
        existing_map = await self.repo.get_existing_targets_for_parent(parent_id)
        existing_targets = set(existing_map.keys())

        # 2. Identify what SHOULD exist (from code)
        # ResolvedCalls are already unique by target_id from the ResolverService
        code_targets = {c.target_id for c in resolved_calls}

        # 3. Calculate Diff
        to_create_ids = code_targets - existing_targets
        to_keep_ids = code_targets & existing_targets
        to_delete_targets = existing_targets - code_targets

        # 4. Action: Delete Stale
        if to_delete_targets:
            call_ids_to_remove = [existing_map[tid]
                                  for tid in to_delete_targets]
            await self.repo.batch_delete_calls(call_ids_to_remove)
            logger.debug(
                f"Removed {len(call_ids_to_remove)} stale calls from {parent_node.qname}")

        # 5. Action: Create New
        if to_create_ids:
            calls_to_create = [
                {
                    "name": c.call_node_name,
                    "target_id": c.target_id,
                    "description": f"call{parent_node.qname}::{c.target_qname}",
                    "position": c.position
                }
                for c in resolved_calls
                if c.target_id in to_create_ids
            ]
            created_map = await self.repo.batch_create_call_nodes(parent_id, calls_to_create)

            logger.debug(
                f"Created {len(calls_to_create)} new calls in {parent_node.qname}")

        # Build a map of ALL active targets (retained + newly added)
        # This is the "Merge Sync" key: we need to recurse for everything currently in code
        active_call_map = {**existing_map, **created_map}
        # Filter to only include targets present in the current code resolution
        active_call_map = {tid: cid for tid, cid in active_call_map.items() if tid in code_targets}

        return ScopeSyncResult(
            parent_id=parent_id,
            created_map=active_call_map,  # Now contains all active mappings
            added_target_ids=to_create_ids,
            retained_target_ids=to_keep_ids,
            removed_target_ids=to_delete_targets
        )
