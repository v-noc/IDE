from arango.database import StandardDatabase

from app.core.model import AllNodes, edges
from app.core.repository.base.node_repo import NodeRepository
from app.core.repository.base.edge_repo import EdgeRepository

from .project_repo import ProjectRepo
from .folder_repo import FolderRepo
from .file_repo import FileRepo
from .code_elements.function_repo import FunctionRepo
from .code_elements.class_repo import ClassRepo
from .code_elements.call_repo import CallRepo
from .log_repo import LogRepository
from .document_repo import DocumentRepo
from .group_repo import GroupRepo


class Repositories:
    """A container for all repository instances."""

    def __init__(self, db: StandardDatabase):
        # Generic Node Repo for mixed-type queries
        self.nodes = NodeRepository(db, "nodes", AllNodes)

        # Specific Node Repos for type-specific operations
        self.project_repo = ProjectRepo(db)
        self.folder_repo = FolderRepo(db)
        self.file_repo = FileRepo(db)
        self.function_repo = FunctionRepo(db)
        self.class_repo = ClassRepo(db)
        self.call_repo = CallRepo(db)
        self.group_repo = GroupRepo(db)
        self.log_repo = LogRepository(db)
        self.document_repo = DocumentRepo(db)

        # Edge Repositories
        self.contains_edges = EdgeRepository[edges.ContainsEdge](
            db, "contains_edges", edges.ContainsEdge)
        self.targets_edges = EdgeRepository[edges.TargetsEdge](
            db,
            "targets_edges",
            edges.TargetsEdge
        )

        # Log edges
        self.log_to_function_edges = EdgeRepository[edges.LogToFunctionEdge](
            db, "log_to_function_edges",
            edges.LogToFunctionEdge
        )
        self.log_to_log_edges = EdgeRepository[edges.LogToLogEdge](
            db, "log_to_log_edges",
            edges.LogToLogEdge
        )
        # self.imports_edges = BaseRepository(
        #     db, "imports_edges", edges.ImportsEdge, is_edge=True
        # )
