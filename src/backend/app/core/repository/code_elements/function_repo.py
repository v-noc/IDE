from app.core.repository.base.node_repo import NodeRepository
from app.core.model.nodes import FunctionNode
from arangoasync.database import AsyncDatabase


class FunctionRepo(NodeRepository[FunctionNode]):
    def __init__(self, db: AsyncDatabase):
        super().__init__(db, "nodes", FunctionNode)
