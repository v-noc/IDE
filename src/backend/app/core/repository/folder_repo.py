from .base.node_repo import NodeRepository
from app.core.model.nodes import FolderNode
from arangoasync.database import AsyncDatabase


class FolderRepo(NodeRepository[FolderNode]):
    def __init__(self, db: AsyncDatabase):
        super().__init__(db, "nodes", FolderNode)
