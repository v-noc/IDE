"""
The Project domain object, representing the root of a code graph.
"""
from typing import Dict, Any, Optional
from .base import DomainObject
from .file import File
from .folder import Folder
from .virtual_folder import VirtualFolder
from .code_elements import to_domain_element
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
    def key(self) -> str:
        return self.model.key

    @property
    def absolute_path(self) -> str:
        return self.path + self.name

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "name": self.name,
            "node_type": self.model.node_type,
            "icon": self.model.icon,
            "theme": (
                self.model.properties.metaData.model_dump()
                if self.model.properties.metaData
                else None
            ),
            "path": self.path,
            "description": self.model.description,
        }

    def update(self, name: str, path: str) -> None:
        """Updates the project's name and path."""
        self.model.name = name

        self.model.properties.path = path
        db.nodes.update(self.model)

    def add_file(self, file_name: str, file_path: str) -> File:
        """Adds a new file directly to the project's root."""
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

        # 2. Create the ContainsEdge to link it to this project
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

    def add_folder(self, folder_name: str, folder_path: str) -> Folder:
        """Adds a new folder directly to the project's root."""
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

        # 2. Create the ContainsEdge to link it to this project
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

    def add_virtual_folder(
        self, folder_name: str, description: Optional[str] = None
    ) -> VirtualFolder:
        """Adds a new virtual folder directly to the project's root."""
        virtual_folder = node.VirtualFolderNode(
            name=folder_name,
            qname=f"{self.qname}.{folder_name}",
            description=description
        )
        created_virtual_folder = db.nodes.create(virtual_folder)
        contains_edge_model = edges.VirtualContainsEdge(
            _from=self.id,
            _to=created_virtual_folder.id,
        )
        db.virtual_contains_edges.create(contains_edge_model)
        return VirtualFolder(created_virtual_folder)

    def get_virtual_folders(self) -> list[VirtualFolder]:
        """
        Retrieves all virtual folders contained within the project.
        """
        virtual_folder_nodes = db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.virtual_contains_edges,
            filter_by_type="virtual_folder",
        )
        return [VirtualFolder(node) for node in virtual_folder_nodes]

    def get_files(self) -> list[File]:
        """Retrieves all files directly contained within the project."""
        file_nodes = db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.contains_edges,
            filter_by_type="file"
        )
        return [File(node) for node in file_nodes]

    def get_all_folders(self) -> list[Folder]:
        """Retrieves all folders directly contained within the project."""
        folder_nodes = db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.contains_edges,
            filter_by_type="folder",
            limit=100,
        )
        return [Folder(node) for node in folder_nodes]

    def get_folders(self) -> list[Folder]:
        """Retrieves all folders directly contained within the project."""
        folder_nodes = db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.contains_edges,
            filter_by_type="folder"
        )
        return [Folder(node) for node in folder_nodes]

    def get_descendant_tree(
        self, with_dependency_tree: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieves all descendants of this project and formats them as a tree.
        Ensures each node is serialized via its domain object's to_dict().
        """
        cursor = db.contains_edges.get_descendant_tree_query(self.id)

        def serialize_node(node_data: dict) -> dict:
            node_type = node_data.get("node_type")
            if node_type == "folder":
                model = node.FolderNode.model_validate(node_data)
                return Folder(model).to_dict()
            if node_type == "file":
                model = node.FileNode.model_validate(node_data)
                return File(model).to_dict()
            if node_type in {"function", "class"}:
                model_cls = (
                    node.FunctionNode
                    if node_type == "function"
                    else node.ClassNode
                )
                model = model_cls.model_validate(node_data)
                domain_element = to_domain_element(model)
                return (
                    domain_element.to_dict(with_dependency_tree=True)
                    if domain_element
                    else node_data
                )
            # Fallback
            return node_data

        node_map = {
            self.id: {
                "node": {**self.to_dict(), "id": self.id},
                "children": [],
            }
        }

        for item in cursor:
            node_data = item['vertex']
            parent_id = item['parent_id']

            node_id = node_data['_id']
            if node_id not in node_map:
                serialized = serialize_node(node_data)
                # Guarantee children are built here
                if not serialize_node(node_data).get("children"):
                    serialized["children"] = []
                # Ensure id is present for build traversal
                if "id" not in serialized:
                    serialized["id"] = node_id
                node_map[node_id] = {"node": serialized, "children": []}

            if parent_id in node_map:
                node_map[parent_id]["children"].append(node_map[node_id])

        def build_tree(node_id: str) -> Dict[str, Any]:
            node_info = node_map[node_id]
            node_payload = node_info["node"]

            # If the node (typically function/class) already carries a
            # dependency-tree children list from its domain serialization,
            # preserve it as-is.
            provided_children = node_payload.get("children")
            if provided_children:
                return {
                    **node_payload,
                    "children": provided_children,
                }

            # Otherwise, build children from the structural contains traversal
            return {
                **node_payload,
                "children": [
                    build_tree(
                        child["node"]["id"]
                    )
                    for child in node_info["children"]
                ],
            }

        return build_tree(self.id)
