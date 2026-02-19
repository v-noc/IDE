import logging
import uuid
from typing import Awaitable, Callable, List, Optional, Tuple
from .models import ResolvedCall, ScopeSyncResult
from app.core.services.call_service import CallService
from app.core.model.schemas.code_element_schema import CallSchema
from app.core.model.nodes import CallNode, ProjectNode


logger = logging.getLogger(__name__)


class ScopeProcessor:
    def __init__(self, service: CallService):
        self.call_service = service

    async def sync_scope(
        self,
        parent_node: any,
        resolved_calls: List[ResolvedCall],
        parent_call_node_id: Optional[str] = None,
        new_branch: Optional[str] = None,
        insert_batch_setter: Optional[Callable[[
            List[CallNode], Optional[str]], Awaitable[None]]] = None,
        move_batch_setter: Optional[Callable[[
            List[Tuple[str, str, str]]], Awaitable[None]]] = None,
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
        existing_children = await self.call_service.get_direct_call_children(parent_id, CallSchema.__name__)

        existing_map = {}
        for child in existing_children:
            existing_map[child["target"]["_id"]] = child["call"]["_id"]

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
            await self.call_service.batch_delete(call_ids_to_remove)
            logger.debug(
                f"Removed {len(call_ids_to_remove)} stale calls from {parent_node.qname}")

        # 5. Action: Create New
        if to_create_ids:

            calls_to_create = [
                CallNode(
                    id=f"{CallSchema.__name__}/{str(uuid.uuid4())}",
                    qname=f"{parent_node.id.split('/')[-1]}::{c.target_id.split('/')[-1]}",
                    name=c.call_node_name,
                    target_function=c.target_id,
                    description=f"call{parent_node.qname}::{c.target_qname}",

                )
                for c in resolved_calls
                if c.target_id in to_create_ids
            ]
            if insert_batch_setter:
                await insert_batch_setter(calls_to_create, new_branch)
            else:
                await self.call_service.create_batch(calls_to_create, branch_name=new_branch)

            created_map = {c.target_function: c.id for c in calls_to_create}

            moves_to_execute = [
                (c.id, parent_id, "call") for c in calls_to_create
            ]
            if move_batch_setter:
                await move_batch_setter(moves_to_execute)
            else:
                await self.call_service.move_batch(moves_to_execute)

            logger.debug(
                f"Created {len(calls_to_create)} new calls in {parent_node.qname}")

        # Build a map of ALL active targets (retained + newly added)
        # This is the "Merge Sync" key: we need to recurse for everything currently in code
        active_call_map = {**existing_map, **created_map}
        # Filter to only include targets present in the current code resolution
        active_call_map = {tid: cid for tid,
                           cid in active_call_map.items() if tid in code_targets}

        return ScopeSyncResult(
            parent_id=parent_id,
            created_map=active_call_map,  # Now contains all active mappings
            added_target_ids=to_create_ids,
            retained_target_ids=to_keep_ids,
            removed_target_ids=to_delete_targets
        )
