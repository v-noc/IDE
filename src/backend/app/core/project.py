"""
The Project domain object, representing the root of a code graph.
"""
from .base import DomainObject
from .file import File
from .folder import Folder
from ..models import node, edges, properties
from ..db import collections as db

class Project(DomainObject[node.ProjectNode]):
    """
    A domain object representing a project, which is the root container for
    all other code elements in the graph.
    """
    @property
    def name(self) -> str:
        return self.model.name

    @property
    def path(self) -> str:
        return self.model.properties.path

    def add_file(self, file_name: str, file_path: str) -> File:
        """Adds a new file directly to the project's root."""
        # 1. Create the FileNode model
        file_node_model = node.FileNode(
            name=file_name,
            qname=file_path,
            node_type="file",
            properties=properties.FileProperties(path=file_path)
        )
        created_file_node = db.nodes.create(file_node_model)

        # 2. Create the ContainsEdge to link it to this project
        contains_edge_model = edges.ContainsEdge(
            _from=self.id,
            _to=created_file_node.id,
            position=node.NodePosition(line_no=0, col_offset=0, end_line_no=0, end_col_offset=0)
        )
        db.contains_edges.create(contains_edge_model)

        # 3. Return the hydrated File domain object
        return File(created_file_node)

    def add_folder(self, folder_name: str, folder_path: str) -> Folder:
        """Adds a new folder directly to the project's root."""
        # 1. Create the FolderNode model
        folder_node_model = node.FolderNode(
            name=folder_name,
            qname=folder_path,
            node_type="folder",
            properties=properties.FolderProperties(path=folder_path)
        )
        created_folder_node = db.nodes.create(folder_node_model)

        # 2. Create the ContainsEdge to link it to this project
        contains_edge_model = edges.ContainsEdge(
            _from=self.id,
            _to=created_folder_node.id,
            position=node.NodePosition(line_no=0, col_offset=0, end_line_no=0, end_col_offset=0)
        )
        db.contains_edges.create(contains_edge_model)

        # 3. Return the hydrated Folder domain object
        return Folder(created_folder_node)