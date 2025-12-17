import logging
from typing import Any, Dict, List, Optional

from arango.database import StandardDatabase

from app.core.model.nodes import CallNode, ClassNode, FunctionNode
from app.core.repository.base.node_repo import NodeRepository

logger = logging.getLogger(__name__)


class CallRepo(NodeRepository[CallNode]):
    def __init__(self, db: StandardDatabase):
        super().__init__(db, "nodes", CallNode)

    async def get_target(self, call_node_id: str) -> Optional[ClassNode | FunctionNode]:
        """Find the function or class that this CallNode targets.

        Avoids truthiness/len checks on Arango Cursor to prevent
        CursorCountError by consuming at most one document.
        """
        query = """
            FOR target IN 1..1 OUTBOUND @start_node_id targets_edges
                LIMIT 1
                RETURN target
        """
        bind_vars = {
            "start_node_id": call_node_id,
        }
        cursor = await self.db.aql.execute(query, bind_vars=bind_vars)
        doc = await cursor.next() if cursor else None
        if not doc:
            return None
        node_type = doc.get("node_type")
        if node_type == "function":
            return FunctionNode.model_validate(doc)
        if node_type == "class":
            return ClassNode.model_validate(doc)
        return None

    async def find_call_by_target_parent(
        self,
        target_id: str,
        parent_id: str,
    ) -> Optional[CallNode]:
        """
        Find call node by parent and target.
        Original approach but with early LIMIT to stop scanning.
        """
        query = """
        FOR c IN 1..1 OUTBOUND @parent_id contains_edges
            FILTER c.node_type == "call"
            LET t = FIRST(
                FOR target IN 1..1 OUTBOUND c targets_edges
                    RETURN target
            )
            FILTER t != null && t._id == @target_id
            LIMIT 1
            RETURN c
        """

        bind_vars = {"target_id": str(target_id), "parent_id": str(parent_id)}

        try:
            cursor = await self.db.aql.execute(
                query,
                bind_vars=bind_vars,
                batch_size=1,
            )

            doc = await cursor.next() if cursor else None
            if not doc:
                return None
            return CallNode(**doc)

        except Exception as e:
            logger.error("Error finding call by target/parent: %s", e)
            return None

    async def find_calls_by_target_parent_batch(
        self,
        parent_target_pairs: List[tuple[str, str]],
    ) -> Dict[tuple[str, str], Optional[CallNode]]:
        """
        Batch find call nodes by (parent_id, target_id) pairs.
        Returns dict mapping (parent_id, target_id) -> CallNode or None.
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
                # Skip null rows (when FIRST() returns null for no match)
                if row is None:
                    continue
                # Ensure row has required fields
                if "parent_id" not in row or "target_id" not in row:
                    continue
                # Skip if call is None or missing
                if not row.get("call"):
                    continue
                key = (row["parent_id"], row["target_id"])
                results[key] = CallNode(**row["call"])

            return results

        except Exception as e:
            logger.error(
                f"Error batch finding calls by target/parent: {e} - {len(parent_target_pairs)}")
            # Fallback: return None for all
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

        Logic:
        - Start from the given parent node id.
        - Walk INBOUND on ``contains_edges`` while the current vertex is a
          ``call`` node.
        - For every such call, look at its target via ``targets_edges``.
        - If the target's ``_id`` matches ``target_id``, increment the count.
        - Stop as soon as we reach a non-call node or ``max_depth``.

        Args:
            parent_id: Node id to start from (usually the parent of a call).
            target_id: The function/class node id we consider "the same" for
                       recursion purposes.
            max_depth: Safety limit on how far up the chain we walk.

        Returns:
            Integer count of recursive calls found on the upward chain.
        """
        query = """
            LET matches = (
                FOR v IN 0..@max_depth INBOUND @start_parent_id @@contains
                    PRUNE v.node_type != "call"
                    FILTER v.node_type == "call"
                    LET target = FIRST(
                        FOR t IN 1..1 OUTBOUND v @@targets
                            RETURN t
                    )
                    FILTER target != null && target._id == @target_id
                    RETURN 1
            )
            RETURN LENGTH(matches)
        """

        bind_vars = {
            "start_parent_id": str(parent_id),
            "target_id": str(target_id),
            "@contains": "contains_edges",
            "@targets": "targets_edges",
            "max_depth": max_depth,
        }

        try:
            cursor = await self.db.aql.execute(query, bind_vars=bind_vars)
            result = await cursor.next() if cursor else 0
            return int(result or 0)
        except Exception as e:
            logger.error(
                "Error counting recursive calls upward for %s -> %s: %s",
                parent_id,
                target_id,
                e,
            )
            return 0

    async def count_recursive_calls_upward_batch(
        self,
        parent_target_pairs: List[tuple[str, str]],
        max_depth: int = 50,
    ) -> Dict[tuple[str, str], int]:
        """
        Batch version of count_recursive_calls_upward.
        Counts recursion for multiple (parent_id, target_id) pairs at once.

        Args:
            parent_target_pairs: List of (parent_id, target_id) tuples to check.
            max_depth: Safety limit on how far up the chain we walk.

        Returns:
            Dict mapping (parent_id, target_id) -> recursion count.
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
            # Fallback: return 0 for all
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
