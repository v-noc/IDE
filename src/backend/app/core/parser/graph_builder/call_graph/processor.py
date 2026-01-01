import logging
from typing import List, Set
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
        resolved_calls: List[ResolvedCall]
    ) -> ScopeSyncResult:
        """
        Synchronizes the DB for a specific parent node.
        Ensures exactly one CallNode exists per unique target_id.
        """

        parent_id = parent_node.id

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
            print(f"created_map: {parent_node.qname} <-> {created_map}")
            logger.debug(
                f"Created {len(calls_to_create)} new calls in {parent_node.qname}")

        return ScopeSyncResult(
            parent_id=parent_id,
            added_target_ids=to_create_ids,
            retained_target_ids=to_keep_ids,
            removed_target_ids=to_delete_targets
        )
