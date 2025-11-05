from app.core.model.nodes import CallNode, ClassNode, FunctionNode
from app.core.repository.base.node_repo import NodeRepository
from arango.database import StandardDatabase
from typing import Optional, List, Dict, Any


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

        query = """
        FOR c IN nodes
            FILTER c.node_type == "call"
            LET t = FIRST(
                FOR target IN 1..1 OUTBOUND c targets_edges
                    RETURN target
            )
            LET p = FIRST(
                FOR v, e IN 1..1 INBOUND c contains_edges
                    RETURN e._from
            )
            FILTER t != null && t._id == @target_id && p == @parent_id
            LIMIT 1
            RETURN c
        """

        # Create bind variables with explicit type conversion
        bind_vars = {
            "target_id": str(target_id),
            "parent_id": str(parent_id)
        }

        # Add debug logging for bind variables

        try:
            # Try direct execution with maximum debug options
            cursor = self.db.aql.execute(
                query,
                bind_vars=bind_vars,
                count=True,
                batch_size=1,
                ttl=60,
                fail_on_warning=False
            )

            # Process results explicitly
            results = []
            for doc in cursor:
                results.append(doc)

            if not results:
                return None
            return CallNode(**results[0])

        except Exception as e:
            # Comprehensive error analysis
            error_info = {
                "query": query,
                "bind_vars": bind_vars,
                "error_message": str(e),
                "error_type": type(e).__name__,
                "db_version": self.db.version(),
                "collections": self.db.collections()
            }

            print(f"ERROR ANALYSIS: {error_info}")
            raise

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
