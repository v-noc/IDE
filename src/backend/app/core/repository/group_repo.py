from app.core.repository.base.node_repo import NodeRepository
from app.core.model.nodes import GroupNode
from arango.database import StandardDatabase


class GroupRepo(NodeRepository[GroupNode]):
    def __init__(self, db: StandardDatabase):
        super().__init__(db, "nodes", GroupNode)
