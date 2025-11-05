from .base.node_repo import NodeRepository
from app.core.model.nodes import FolderNode
from arango.database import StandardDatabase


class FolderRepo(NodeRepository[FolderNode]):
    def __init__(self, db: StandardDatabase):
        super().__init__(db, "nodes", FolderNode)
