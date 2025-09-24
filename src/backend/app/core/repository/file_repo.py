from .base.node_repo import NodeRepository
from app.core.model.nodes import FileNode
from arango.database import StandardDatabase


class FileRepo(NodeRepository[FileNode]):
    def __init__(self, db: StandardDatabase):
        super().__init__(db, "nodes", FileNode)
