import logging

from app.core.model.nodes import CallNode, ClassNode, FunctionNode
from app.core.repository.base.node_repo import NodeRepository
from arango.database import StandardDatabase
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class CallRepo(NodeRepository[CallNode]):
    def __init__(self, db: StandardDatabase):
        super().__init__(db, "nodes", CallNode)

    def get_target(
        self, call_node_id: str
    ) -> Optional[ClassNode | FunctionNode]:
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
        cursor = self.db.aql.execute(query, bind_vars=bind_vars)
        doc = next(cursor, None)
        if not doc:
            return None
        node_type = doc.get("node_type")
        if node_type == "function":
            return FunctionNode.model_validate(doc)
        if node_type == "class":
            return ClassNode.model_validate(doc)
        return None

    def find_call_by_target_parent(
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

        bind_vars = {
            "target_id": str(target_id),
            "parent_id": str(parent_id)
        }

        try:
            cursor = self.db.aql.execute(
                query,
                bind_vars=bind_vars,
                batch_size=1,
            )

            doc = next(cursor, None)
            if not doc:
                return None
            return CallNode(**doc)

        except Exception as e:
            logger.error(
                "Error finding call by target/parent: %s", e
            )
            return None

    def find_calls_by_target_parent_batch(
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
            FOR call IN 1..1 OUTBOUND pair.parent_id contains_edges
                FILTER call.node_type == "call"
                LET target = FIRST(
                    FOR t IN 1..1 OUTBOUND call targets_edges
                        RETURN t
                )
                FILTER target != null && target._id == pair.target_id
                LIMIT 1
                RETURN {
                    parent_id: pair.parent_id,
                    target_id: pair.target_id,
                    call: call
                }
        """

        bind_vars = {
            "pairs": [
                {"parent_id": str(p), "target_id": str(t)}
                for p, t in parent_target_pairs
            ]
        }

        try:
            cursor = self.db.aql.execute(query, bind_vars=bind_vars)
            results = {}

            # Initialize all pairs to None
            for parent_id, target_id in parent_target_pairs:
                results[(parent_id, target_id)] = None

            # Fill in found calls
            for row in cursor:
                key = (row["parent_id"], row["target_id"])
                results[key] = CallNode(**row["call"])

            return results

        except Exception as e:
            logger.error(
                "Error batch finding calls by target/parent: %s", e
            )
            # Fallback: return None for all
            return {
                (p, t): None for p, t in parent_target_pairs
            }

    def get_downward_call_chain(self, node_id: str) -> List[Dict[str, Any]]:
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
        cursor = self.db.aql.execute(query, bind_vars=bind_vars)
        return list(cursor)

    def find_upward_call_chain(self, call_id: str) -> List[Dict[str, Any]]:
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
        cursor = self.db.aql.execute(query, bind_vars=bind_vars)
        return list(cursor)
