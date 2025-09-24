from app.core.repository.base.node_repo import NodeRepository
from app.core.model.nodes import ClassNode
from arango.database import StandardDatabase
from typing import List
from app.core.model.nodes import CallNode


class ClassRepo(NodeRepository[ClassNode]):
    def __init__(self, db: StandardDatabase):
        super().__init__(db, "nodes", ClassNode)

    def find_callers(self, function_id: str) -> List[CallNode]:
        """Finds all CallNodes that target this function."""
        query = """
        FOR caller IN 1..1 INBOUND @start_node_id @@targets_collection
            FILTER caller.node_type == 'call'
            RETURN caller
        """
        bind_vars = {
            "start_node_id": function_id,
            "@targets_collection": "targets",
        }
        # The core repo executes the query, but the LOGIC lives here.
        callers = self._nodes.aql(query, bind_vars)
        return [c for c in callers if isinstance(c, CallNode)]
