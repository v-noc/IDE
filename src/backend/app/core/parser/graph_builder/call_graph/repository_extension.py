from typing import List, Set, Dict, Tuple
from app.core.model.nodes import CallNode
from app.core.repository.base.base_node_repo import BaseNodeRepository


class CallGraphRepository:
    """
    Extensions for CallRepo to handle batch graph operations.
    Integrate this into your existing Repositories class or CallRepo.
    """

    def __init__(self, db):
        self.db = db
        self.collection_name = "nodes"

    async def get_existing_targets_for_parent(self, parent_id: str) -> Dict[str, str]:
        """
        Returns a map of {target_id: call_node_id} for all calls originating 
        from the given parent.
        """
        query = """
            FOR c IN 1..1 OUTBOUND @parent_id contains_edges
                FILTER c.node_type == "call"
                LET target = FIRST(
                    FOR t IN 1..1 OUTBOUND c targets_edges RETURN t
                )
                FILTER target != null
                RETURN { target_id: target._id, call_id: c._id }
        """
        cursor = await self.db.aql.execute(query, bind_vars={"parent_id": parent_id})
        result = {}
        async for doc in cursor:
            result[doc["target_id"]] = doc["call_id"]
        return result

    async def batch_create_call_nodes(
        self,
        parent_id: str,
        calls_data: List[dict]
    ) -> None:
        """
        Creates CallNodes, attaches them to Parent, and links them to Target.
        calls_data = [{ "name":..., "target_id":..., "position":... }]
        """
        if not calls_data:
            return

        # We execute a transaction-like AQL script for atomicity
        query = """
        FOR data IN @calls_data
            // 1. Create Call Node
            INSERT {
                name: data.name,
                qname: CONCAT(@parent_id, "::", data.target_id),
                node_type: "call",
                description: data.description,
                position: data.position,
                status: "active",
                created_at: DATE_ISO8601(DATE_NOW()),
                updated_at: DATE_ISO8601(DATE_NOW())
            } INTO nodes LET new_node = NEW

            // 2. Link Parent -> Call (Contains)
            INSERT { _from: @parent_id, _to: new_node._id } INTO contains_edges

            // 3. Link Call -> Target (Targets)
            INSERT { _from: new_node._id, _to: data.target_id } INTO targets_edges

            // 4. RETURN MAPPING
            RETURN { target_id: data.target_id, call_id: new_node._id }
        """

        # Serialize Pydantic position to dict if needed
        serialized_data = []
        for c in calls_data:
            item = c.copy()
            if hasattr(item['position'], 'model_dump'):
                item['position'] = item['position'].model_dump()
            serialized_data.append(item)

        cursor = await self.db.aql.execute(
            query,
            bind_vars={
                "parent_id": parent_id,
                "calls_data": serialized_data
            }
        )
        created_map = {}
        async for doc in cursor:
            created_map[doc["target_id"]] = doc["call_id"]

        return created_map

    async def batch_delete_calls(self, call_ids: List[str]) -> None:
        """
        Removes CallNodes and their associated edges safely.
        Uses 'ignoreErrors: true' to prevent crashes if records are already deleted.
        """
        if not call_ids:
            return

        query = """
            FOR call_id IN @call_ids
                // 1. Collect and remove incoming contains_edges (parent -> call)
                LET contain_keys = (
                    FOR e IN contains_edges
                        FILTER e._to == call_id
                        RETURN e._key
                )
                FOR ck IN contain_keys
                    REMOVE ck IN contains_edges OPTIONS { ignoreErrors: true }

                // 2. Collect and remove outgoing targets_edges (call -> target)
                LET target_keys = (
                    FOR e IN targets_edges
                        FILTER e._from == call_id
                        RETURN e._key
                )
                FOR tk IN target_keys
                    REMOVE tk IN targets_edges OPTIONS { ignoreErrors: true }

                // 3. Remove the call node itself
                REMOVE call_id IN nodes OPTIONS { ignoreErrors: true }
        """

        await self.db.aql.execute(query, bind_vars={"call_ids": call_ids})
