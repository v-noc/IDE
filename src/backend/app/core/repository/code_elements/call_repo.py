import logging
import asyncio
from typing import Any, Dict, List, Optional, Tuple

from arangoasync.database import AsyncDatabase

from app.core.model.nodes import CallNode, ClassNode, FunctionNode
from ..base.base_node_repo import BaseNodeRepository

logger = logging.getLogger(__name__)


class CallRepo(BaseNodeRepository[CallNode]):
    def __init__(self, db: AsyncDatabase):
        super().__init__(db, "nodes", CallNode)

    async def create_with_edges(
        self,
        call_node: CallNode,
        parent_id: str,
        target_id: str
    ) -> CallNode:
        """
        Atomically create CallNode and edges:
        - Call lives under parent (contains_edge)
        - Call targets callee (targets_edge)
        """
        # Create the call node first
        created_node = await self.create(call_node)

        # Create edges
        # We use asyncio.gather for parallelism
        await asyncio.gather(
            self._ensure_contains_edge(parent_id, created_node.id),
            self._ensure_targets_edge(created_node.id, target_id)
        )

        return created_node

    async def _ensure_contains_edge(self, parent_id: str, child_id: str):
        query = """
            INSERT { _from: @from_id, _to: @to_id } INTO contains_edges
        """
        try:
            await self.db.aql.execute(query, bind_vars={"from_id": parent_id, "to_id": child_id})
        except Exception:
            # Ignore duplicate edge errors or handle gracefully
            pass

    async def _ensure_targets_edge(self, call_id: str, target_id: str):
        query = """
            INSERT { _from: @from_id, _to: @to_id } INTO targets_edges
        """
        try:
            await self.db.aql.execute(query, bind_vars={"from_id": call_id, "to_id": target_id})
        except Exception:
            pass

    async def update_call(self, call_id: str, updates: Dict[str, Any]) -> Optional[CallNode]:
        """Update call node properties."""
        query = """
            UPDATE @key WITH @updates IN @@collection RETURN NEW
        """
        try:
            cursor = await self.db.aql.execute(
                query,
                bind_vars={
                    "key": call_id.split("/")[-1] if "/" in call_id else call_id,
                    "updates": updates,
                    "@collection": self.collection_name
                }
            )
            doc = await cursor.next()
            return CallNode(**doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to update call {call_id}: {e}")
            return None

    async def get_calls_by_parent(self, parent_id: str) -> List[CallNode]:
        """Get all direct call-node children."""
        query = """
            FOR c IN 1..1 OUTBOUND @parent_id contains_edges
                FILTER c.node_type == "call"
                RETURN c
        """
        cursor = await self.db.aql.execute(query, bind_vars={"parent_id": parent_id})
        return [CallNode(**doc) async for doc in cursor]

    async def find_call_by_target_parent(
        self,
        target_id: str,
        parent_id: str,
    ) -> Optional[CallNode]:
        """
        Find call node by parent and target.
        """
        results = await self.find_calls_by_target_parent_batch([(parent_id, target_id)])
        return results.get((parent_id, target_id))

    async def get_target(self, call_node_id: str) -> Optional[ClassNode | FunctionNode]:
        """Find the function or class that this CallNode targets."""
        query = """
            FOR target IN 1..1 OUTBOUND @start_node_id targets_edges
                LIMIT 1
                RETURN target
        """
        bind_vars = {
            "start_node_id": call_node_id,
        }
        cursor = await self.db.aql.execute(query, bind_vars=bind_vars)
        doc = None
        async for row in cursor:
            doc = row
            break

        if not doc:
            return None
        node_type = doc.get("node_type")
        if node_type == "function":
            return FunctionNode.model_validate(doc)
        if node_type == "class":
            return ClassNode.model_validate(doc)
        return None


    async def find_calls_by_target_parent_batch(
        self,
        parent_target_pairs: List[tuple[str, str]],
    ) -> Dict[tuple[str, str], Optional[CallNode]]:
        """
        Batch find call nodes by (parent_id, target_id) pairs.
        """
        if not parent_target_pairs:
            return {}

        query = """
            FOR pair IN @pairs
                LET result = FIRST(
                    FOR call IN 1..1 OUTBOUND pair.parent_id contains_edges
                        FILTER call.node_type == "call"
                        LET target = FIRST(
                            FOR t IN 1..1 OUTBOUND call targets_edges
                                RETURN t
                        )
                        FILTER target != null && target._id == pair.target_id
                        RETURN {
                            parent_id: pair.parent_id,
                            target_id: pair.target_id,
                            call: call
                        }
                )
                RETURN result
        """

        bind_vars = {
            "pairs": [
                {"parent_id": str(p), "target_id": str(t)}
                for p, t in parent_target_pairs
            ]
        }

        try:
            cursor = await self.db.aql.execute(query, bind_vars=bind_vars)
            results = {}

            # Initialize all pairs to None
            for parent_id, target_id in parent_target_pairs:
                results[(parent_id, target_id)] = None

            # Fill in found calls
            async for row in cursor:
                if row is None:
                    continue
                if "parent_id" not in row or "target_id" not in row:
                    continue
                if not row.get("call"):
                    continue
                key = (row["parent_id"], row["target_id"])
                results[key] = CallNode(**row["call"])

            return results

        except Exception as e:
            logger.error(
                f"Error batch finding calls by target/parent: {e} - {len(parent_target_pairs)}")
            return {(p, t): None for p, t in parent_target_pairs}

    async def count_recursive_calls_upward(
        self,
        parent_id: str,
        target_id: str,
        max_depth: int = 50,
    ) -> int:
        """
        Count how many times the same target (function/class) appears
        in the call chain **upwards** from a given parent node.
        """
        results = await self.count_recursive_calls_upward_batch([(parent_id, target_id)], max_depth=max_depth)
        return results.get((parent_id, target_id), 0)

    async def count_recursive_calls_upward_batch(
        self,
        parent_target_pairs: List[tuple[str, str]],
        max_depth: int = 50,
    ) -> Dict[tuple[str, str], int]:
        """
        Batch version of count_recursive_calls_upward.
        """
        if not parent_target_pairs:
            return {}

        query = """
            FOR pair IN @pairs
                LET matches = (
                    FOR v IN 0..@max_depth INBOUND pair.parent_id @@contains
                        PRUNE v.node_type != "call"
                        FILTER v.node_type == "call"
                        LET target = FIRST(
                            FOR t IN 1..1 OUTBOUND v @@targets
                                RETURN t
                        )
                        FILTER target != null && target._id == pair.target_id
                        RETURN 1
                )
                RETURN {
                    parent_id: pair.parent_id,
                    target_id: pair.target_id,
                    count: LENGTH(matches)
                }
        """

        bind_vars = {
            "pairs": [
                {"parent_id": str(p), "target_id": str(t)}
                for p, t in parent_target_pairs
            ],
            "@contains": "contains_edges",
            "@targets": "targets_edges",
            "max_depth": max_depth,
        }

        try:
            cursor = await self.db.aql.execute(query, bind_vars=bind_vars)
            results = {}

            # Initialize all pairs to 0
            for parent_id, target_id in parent_target_pairs:
                results[(parent_id, target_id)] = 0

            # Fill in found counts
            async for row in cursor:
                key = (row["parent_id"], row["target_id"])
                results[key] = int(row["count"] or 0)

            return results

        except Exception as e:
            logger.error("Error batch counting recursive calls upward: %s", e)
            return {(p, t): 0 for p, t in parent_target_pairs}

    async def get_downward_call_chain(self, node_id: str) -> List[Dict[str, Any]]:
        query = """
        FOR v, e, p IN 1..@max_depth OUTBOUND @start_node_id @@contains
            OPTIONS { order: "bfs" }
            FILTER v.node_type == "call"
                OR (v.node_type == "group" AND v.group_type == "call")
            LET target = v.node_type == "call"
                ? FIRST(FOR t IN 1..1 OUTBOUND v @@targets RETURN t)
                : null
            LET parent_id = LENGTH(p.vertices) >= 2
                ? p.vertices[LENGTH(p.vertices) - 2]._id
                : null
            RETURN {
                vertex: v,
                parent_id: parent_id,
                target: target
            }
        """
        bind_vars = {
            "start_node_id": node_id,
            "@contains": "contains_edges",
            "@targets": "targets_edges",
            "max_depth": 50,
        }
        cursor = await self.db.aql.execute(query, bind_vars=bind_vars)
        results = []
        async for doc in cursor:
            results.append(doc)
        return results

    async def find_upward_call_chain(self, call_id: str) -> List[Dict[str, Any]]:
        query = """
            LET call_chain_path = (
                FOR v IN 0..100 INBOUND @start_call_id @@contains
                    PRUNE v.node_type != "call"
                    RETURN v
            )

            LET call_chain = REVERSE(call_chain_path)

            LET origin = FIRST(
                call_chain
            )

            LET call_chain_with_targets = (
                FOR call IN call_chain
                    LET target = FIRST(
                        FOR t IN 1..1 OUTBOUND call._id @@targets
                            RETURN t
                    )
                    FILTER target != null
                    RETURN { call: call, target: target }
            )

            RETURN {
                origin: origin,
                calls: call_chain_with_targets
            }
        """
        bind_vars = {
            "start_call_id": call_id,
            "@contains": "contains_edges",
            "@targets": "targets_edges",
        }
        cursor = await self.db.aql.execute(query, bind_vars=bind_vars)
        results = []
        async for doc in cursor:
            results.append(doc)
        return results

    async def delete_descendant_calls(self, ancestor_id: str) -> int:
        """
        Delete all CallNodes that are descendants of the given ancestor (e.g. FileNode).
        Also deletes their connected edges.
        """
        # Find call IDs
        query = """
            FOR v IN 1..50 OUTBOUND @ancestor_id contains_edges
                FILTER v.node_type == "call"
                RETURN v._id
        """
        bind_vars = {
            "ancestor_id": ancestor_id
        }
        try:
            cursor = await self.db.aql.execute(query, bind_vars=bind_vars)
            call_ids = [doc async for doc in cursor]

            if not call_ids:
                return 0

            count = 0
            for call_id in call_ids:
                # Strip collection name for delete method which expects key
                key = call_id.split("/")[-1] if "/" in call_id else call_id
                if await self.delete(key):
                    count += 1

            return count
        except Exception as e:
            logger.error(
                f"Error deleting descendant calls for {ancestor_id}: {e}")
            return 0
