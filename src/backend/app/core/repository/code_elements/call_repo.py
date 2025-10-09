from arango.exceptions import AQLQueryExecuteError
from app.core.model.nodes import CallNode, ClassNode, FunctionNode
from app.core.repository.base.node_repo import NodeRepository
from arango.database import StandardDatabase
from typing import Optional


class CallRepo(NodeRepository[CallNode]):
    def __init__(self, db: StandardDatabase):
        super().__init__(db, "nodes", CallNode)

    def get_target(
        self, call_node_id: str
    ) -> Optional[ClassNode | FunctionNode]:
        """Finds the function or class that this CallNode targets."""
        query = """
        FOR target IN 1..1 OUTBOUND @start_node_id @@targets_collection
            LIMIT 1
            RETURN target
        """
        bind_vars = {
            "start_node_id": call_node_id,
            "@targets_collection": "targets_edges",
        }
        results = self._nodes.aql(query, bind_vars)
        return results[0] if results else None

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
        print(f"DEBUG: Bind Variables - {bind_vars}")

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

            print(f"DEBUG: Query returned {(results)} results")
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
