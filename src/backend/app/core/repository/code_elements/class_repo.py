from app.core.repository.base.node_repo import NodeRepository
from app.core.model.nodes import ClassNode
from arango.database import StandardDatabase


class ClassRepo(NodeRepository[ClassNode]):
    def __init__(self, db: StandardDatabase):
        super().__init__(db, "nodes", ClassNode)
