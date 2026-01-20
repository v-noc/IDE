from .base.base_node_repo import BaseNodeRepository
from app.core.model.nodes import GroupNode
from arangoasync.database import AsyncDatabase


class GroupRepo(BaseNodeRepository[GroupNode]):
    def __init__(self, db: AsyncDatabase):
        super().__init__(db, "nodes", GroupNode)
