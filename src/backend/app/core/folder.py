"""
The Folder domain object.
"""
from .base import DomainObject
from .file import File
from .code_elements import to_domain_element
from ..models import node, edges, properties
from ..db import collections as db
from typing import Dict, Any


class Folder(DomainObject[node.FolderNode]):
    """
    A domain object representing a folder, which can contain files and
    other folders.
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

    @property
    def key(self) -> str:
        return self.model.key
    
    def to_dict(self) -> dict:
        return {
            "id": self.model.id,
            "key": self.key,
            "name": self.name,
            "qname": self.model.qname,
            "node_type": self.model.node_type,
            "path": self.path,
            "description": self.model.description,
            "icon": self.model.icon,
            "theme": (
                self.model.properties.metaData.model_dump()
                if self.model.properties.metaData
                else None
            ),
        }

    def add_file(self, file_name: str, file_path: str) -> File:
        """Adds a new file to this folder."""
        # Generate qname using the shared utility method
        file_qname = self._generate_child_qname(file_name, is_file=True)
        
        # 1. Create the FileNode model
        file_node_model = node.FileNode(
            name=file_name,
            qname=file_qname,
            node_type="file",
            properties=properties.FileProperties(path=file_path)
        )
        created_file_node = db.nodes.create(file_node_model)

        # 2. Create the ContainsEdge to link it to this folder
        contains_edge_model = edges.ContainsEdge(
            _from=self.id,
            _to=created_file_node.id,
            position=node.NodePosition(
                line_no=0, col_offset=0, end_line_no=0, end_col_offset=0
            )
        )
        db.contains_edges.create(contains_edge_model)

        # 3. Return the hydrated File domain object
        return File(created_file_node)

    def add_folder(self, folder_name: str, folder_path: str) -> 'Folder':
        """Adds a new sub-folder to this folder."""
        # Generate qname using the shared utility method
        folder_qname = self._generate_child_qname(folder_name)
        
        # 1. Create the FolderNode model
        folder_node_model = node.FolderNode(
            name=folder_name,
            qname=folder_qname,
            node_type="folder",
            properties=properties.FolderProperties(path=folder_path)
        )
        created_folder_node = db.nodes.create(folder_node_model)

        # 2. Create the ContainsEdge to link it to this folder
        contains_edge_model = edges.ContainsEdge(
            _from=self.id,
            _to=created_folder_node.id,
            position=node.NodePosition(
                line_no=0, col_offset=0, end_line_no=0, end_col_offset=0
            )
        )
        db.contains_edges.create(contains_edge_model)

        # 3. Return the hydrated Folder domain object
        return Folder(created_folder_node)

    def get_files(self) -> list[File]:
        """Retrieves all files directly contained within this folder."""
        file_nodes = db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.contains_edges,
            filter_by_type="file"
        )
        return [File(node) for node in file_nodes]

    def get_folders(self) -> list['Folder']:
        """Retrieves all sub-folders directly contained within this folder."""
        folder_nodes = db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.contains_edges,
            filter_by_type="folder"
        )
        return [Folder(node) for node in folder_nodes]

    def get_descendant_tree(self) -> Dict[str, Any]:
        """
        Retrieves all descendants of this folder and formats them as a tree.
        Ensures each node is serialized via its domain object's to_dict().
        """
        cursor = db.contains_edges.get_descendant_tree_query(self.id)
        
        # Root node via domain serialization
        node_map: Dict[str, Dict[str, Any]] = {
            self.id: {"node": self.to_dict(), "children": []}
        }

        def serialize_node(node_data: dict) -> dict:
            node_type = node_data.get("node_type")
            if node_type == "folder":
                model = node.FolderNode.model_validate(node_data)
                return Folder(model).to_dict()
            if node_type == "file":
                model = node.FileNode.model_validate(node_data)
                return File(model).to_dict()
            if node_type in {"function", "class"}:
                # Convert to corresponding domain element (Function/Class)
                # and use its to_dict()
                model_cls = (
                    node.FunctionNode
                    if node_type == "function"
                    else node.ClassNode
                )
                model = model_cls.model_validate(node_data)
                domain_element = to_domain_element(model)
                return (
                    domain_element.to_dict()
                    if domain_element
                    else node_data
                )
            # Fallback: return raw data if unknown
            return node_data
        
        for item in cursor:
            node_data = item['vertex']
            parent_id = item['parent_id']
            
            node_id = node_data['_id']
            if node_id not in node_map:
                serialized = serialize_node(node_data)
                # Children are built here, not nested calls
                serialized["children"] = []
                node_map[node_id] = {"node": serialized, "children": []}
        
            if parent_id in node_map:
                node_map[parent_id]["children"].append(node_map[node_id])

        def build_tree(node_id: str) -> Dict[str, Any]:
            node_info = node_map[node_id]
            return {
                **node_info["node"],
                "children": [
                    build_tree(child["node"]["id"])
                    for child in node_info["children"]
                ]
            }

        return build_tree(self.id)