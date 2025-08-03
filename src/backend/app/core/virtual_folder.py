from .base import DomainObject
from ..models import node, edges
from ..db import collections as db
from typing import Dict, Any, Optional, List
from .virtual_file import VirtualFile


class VirtualFolder(DomainObject[node.VirtualFolderNode]):
    """
    A domain object representing a virtual folder.
    """
    @property
    def key(self) -> str:
        return self.model.key

    @property
    def name(self) -> str:
        return self.model.name

    @property
    def qname(self) -> str:
        return self.model.qname

    @property
    def description(self) -> str | None:
        return self.model.description
    
    @property
    def node_type(self) -> str:
        return self.model.node_type
    
    @staticmethod
    def get_by_key(key: str) -> 'VirtualFolder':
        return VirtualFolder(db.nodes.get(key))

    def delete(self) -> None:
        db.nodes.delete(self.model.key)

    def update(self, update_data: dict) -> 'VirtualFolder':
        updated_model = self.model.model_copy(update=update_data)
        db.nodes.update(updated_model)
        return self.get_by_key(self.key)

    def add_virtual_file(
        self, file_name: str,  description: Optional[str] = None
    ) -> VirtualFile:
        virtual_file = node.VirtualFileNode(
            qname=f"{self.qname}.{file_name}",
            name=file_name,
            description=description
        )
        created_virtual_file = db.nodes.create(virtual_file)
        contains_edge_model = edges.VirtualContainsEdge(
            _from=self.id,
            _to=created_virtual_file.id,
        )
        db.virtual_contains_edges.create(contains_edge_model)
        return VirtualFile(created_virtual_file)

    def get_virtual_files(self) -> List[VirtualFile]:
        return [VirtualFile(file) for file in db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.virtual_contains_edges,
            filter_by_type="virtual_file"
        )]

    def add_virtual_folder(
        self, folder_name: str, description: Optional[str] = None
    ) -> 'VirtualFolder':
        virtual_folder = node.VirtualFolderNode(
            qname=f"{self.qname}.{folder_name}",
            name=folder_name,
            description=description
        )
        created_virtual_folder = db.nodes.create(virtual_folder)
        contains_edge_model = edges.VirtualContainsEdge(
            _from=self.id,
            _to=created_virtual_folder.id,
        )
        db.virtual_contains_edges.create(contains_edge_model)
        return VirtualFolder(created_virtual_folder)

    def get_virtual_folders(self) -> List['VirtualFolder']:
        return [VirtualFolder(folder) for folder in db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.virtual_contains_edges,
            filter_by_type="virtual_folder"
        )]

    def get_descendant_tree(self) -> Dict[str, Any]:
        """
        Retrieves all descendants of this folder and formats them as a tree.
        This implementation uses a single database query for efficiency.
        """
        # This assumes 'virtual_contains_edges' has a 
        # 'get_descendant_tree_query' method, similar to the one used for 
        # real 'contains_edges'.
        cursor = db.virtual_contains_edges.get_descendant_tree_query(self.id)

        node_map = {
            self.id: {
                "node": self.model.model_dump(by_alias=True), "children": []
            }
        }

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
                "children": [
                    build_tree(child["node"]["_id"])
                    for child in node_info["children"]
                ]
            }

        return build_tree(self.id)
