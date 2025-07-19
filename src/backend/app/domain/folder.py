"""
The Folder domain object.
"""
from .container import Container
from .file import File
from ..models.node import Node, NodeType

class Folder(Container):
    """
    A domain object representing a folder, which can contain files and
    other folders.
    """
    def __init__(self, node_data: Node, db_service):
        super().__init__(node=node_data, db_service=db_service)

    @property
    def path(self):
        return self.node.properties.get("path")

    def add_file(self, path: str) -> File:
        """Adds a new file to this folder."""
        file_name = path.split('/')[-1]
        return self._add_element(
            domain_class=File,
            node_type=NodeType.FILE,
            name=file_name,
            qname=path,
            properties={"path": path}
        )

    def add_folder(self, path: str) -> 'Folder':
        """Adds a new sub-folder to this folder."""
        folder_name = path.split('/')[-1]
        return self._add_element(
            domain_class=Folder,
            node_type=NodeType.FOLDER,
            name=folder_name,
            qname=path,
            properties={"path": path}
        )
