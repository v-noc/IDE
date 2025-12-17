from .base.node_repo import NodeRepository
from app.core.model.nodes import FileNode
from arangoasync.database import AsyncDatabase


class FileRepo(NodeRepository[FileNode]):
    def __init__(self, db: AsyncDatabase):
        super().__init__(db, "nodes", FileNode)
