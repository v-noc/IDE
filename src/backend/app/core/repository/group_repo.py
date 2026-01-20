from .base.base_node_repo import NodeRepository
from app.core.model.nodes import GroupNode
from arangoasync.database import AsyncDatabase


class GroupRepo(NodeRepository[GroupNode]):
    def __init__(self, db: AsyncDatabase):
        super().__init__(db, "nodes", GroupNode)
