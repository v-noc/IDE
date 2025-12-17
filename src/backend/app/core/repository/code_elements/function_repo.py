from app.core.repository.base.node_repo import NodeRepository
from app.core.model.nodes import FunctionNode
from arango.database import StandardDatabase


class FunctionRepo(NodeRepository[FunctionNode]):
    def __init__(self, db: StandardDatabase):
        super().__init__(db, "nodes", FunctionNode)
