"""
The Project domain object.
"""
from .container import Container
from .file import File
from .folder import Folder
from ..models.project import Project as ProjectModel
from ..models.node import Node, NodeType, NodePosition

class Project(Container):
    """
    A domain object representing a project, which is the root container for
    all other code elements.
    """
    def __init__(self, project_model: ProjectModel, node_model: Node, db_service):
        super().__init__(node=node_model, db_service=db_service)
        self.project_model = project_model

    @property
    def name(self):
        return self.project_model.name

    @property
    def path(self):
        return self.project_model.path

    def add_file(self, path: str) -> File:
        """Adds a new file to this project."""
        file_name = path.split('/')[-1]
        return self._add_element(
            domain_class=File,
            node_type=NodeType.FILE,
            name=file_name,
            qname=path,
            properties={"path": path}
        )

    def add_folder(self, path: str) -> Folder:
        """Adds a new folder to this project."""
        folder_name = path.split('/')[-1]
        return self._add_element(
            domain_class=Folder,
            node_type=NodeType.FOLDER,
            name=folder_name,
            qname=path,
            properties={"path": path}
        )
