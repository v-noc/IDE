from app.core.model.nodes import CallNode, ClassNode, FunctionNode
from app.core.repository.base.node_repo import NodeRepository
from arango.database import StandardDatabase
from typing import Optional
from app.core.model import AllNodes


class CallRepo(NodeRepository[CallNode]):
    def __init__(self, db: StandardDatabase):
        super().__init__(db, "nodes", CallNode)

    def get_target(self, call_node_id: str) -> Optional[ClassNode | FunctionNode]:
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
