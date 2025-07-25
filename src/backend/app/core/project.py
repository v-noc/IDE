"""
The Project domain object, representing the root of a code graph.
"""
from typing import Dict, Any
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
    
    @property
    def absolute_path(self) -> str:
        return self.path + self.name

    def add_file(self, file_name: str, file_path: str) -> File:
        """Adds a new file directly to the project's root."""
        # Generate qname following the dot notation pattern
        file_qname = file_path.replace(self.path, "").lstrip("/").replace(".py", "").replace("/", ".")
        
        # 1. Create the FileNode model
        file_node_model = node.FileNode(
            name=file_name,
            qname=file_qname,
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
        # Generate qname following the dot notation pattern
        folder_qname = folder_path.replace(self.path, "").lstrip("/").replace("/", ".")
        
        # 1. Create the FolderNode model
        folder_node_model = node.FolderNode(
            name=folder_name,
            qname=folder_qname,
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

    def get_files(self) -> list[File]:
        """Retrieves all files directly contained within the project."""
        file_nodes = db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.contains_edges,
            filter_by_type="file"
        )
        return [File(node) for node in file_nodes]

    def get_folders(self) -> list[Folder]:
        """Retrieves all folders directly contained within the project."""
        folder_nodes = db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.contains_edges,
            filter_by_type="folder"
        )
        return [Folder(node) for node in folder_nodes]
    
    def get_descendant_tree(self) -> Dict[str, Any]:
        """
        Retrieves all descendants of this folder and formats them as a tree.
        """
        cursor = db.contains_edges.get_descendant_tree_query(self.id)
        
        node_map = {self.id: {"node": self.model.model_dump(), "children": []}}
        
        for item in cursor:
            node_data = item['vertex']
            parent_id = item['parent_id']
            
            node_id = node_data['_id']
            if node_id not in node_map:
                node_map[node_id] = {"node": node_data, "children": []}
            
            if parent_id in node_map:
                node_map[parent_id]["children"].append(node_map[node_id])
            
        def build_tree(node_id):
            node_info = node_map[node_id]
            return {
                **node_info["node"],
                "children": [build_tree(child["node"]["_id"]) for child in node_info["children"]]
            }

        return build_tree(self.id)