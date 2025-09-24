from arango.database import StandardDatabase

from app.core.model import nodes, edges
from app.core.repository.base.base_collection import BaseRepository
from app.core.repository.base.node_repo import NodeRepository

from .project_repo import ProjectRepo
from .folder_repo import FolderRepo
from .file_repo import FileRepo
from .code_elements.function_repo import FunctionRepo
from .code_elements.class_repo import ClassRepo
from .code_elements.call_repo import CallRepo


class Repositories:
    """A container for all repository instances."""

    def __init__(self, db: StandardDatabase):
        # Generic Node Repo for mixed-type queries
        self.nodes = NodeRepository(db, "nodes", nodes.BaseNode)

        # Specific Node Repos for type-specific operations
        self.project_repo = ProjectRepo(db)
        self.folder_repo = FolderRepo(db)
        self.file_repo = FileRepo(db)
        self.function_repo = FunctionRepo(db)
        self.class_repo = ClassRepo(db)
        self.call_repo = CallRepo(db)

        # Edge Repositories - YES, you need these!
        self.contains_edges = BaseRepository(
            db, "contains_edges", edges.ContainsEdge, is_edge=True
        )
        self.targets_edges = BaseRepository(
            db, "targets_edges", edges.TargetsEdge, is_edge=True
        )
        # self.imports_edges = BaseRepository(
        #     db, "imports_edges", edges.ImportsEdge, is_edge=True
        # )
