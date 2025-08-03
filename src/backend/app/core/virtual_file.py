from .base import DomainObject
from ..models import node
from ..db import collections as db
from typing import Dict, Any
from .code_elements import Function, Class, Package


class VirtualFile(DomainObject[node.VirtualFileNode]):
    """
    A domain object representing a virtual file.
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
    def get_by_key(key: str) -> 'VirtualFile':
        return VirtualFile(db.nodes.get(key))

    @staticmethod
    def get_by_qname(qname: str) -> 'VirtualFile':
        return VirtualFile(db.nodes.find_one(
            {"qname": qname, "node_type": "virtual_file"}
        ))
    
    def delete(self) -> None:
        db.nodes.delete(self.model.key)

    def update(self, update_data: dict) -> 'VirtualFile':
        updated_model = self.model.model_copy(update=update_data)
        db.nodes.update(updated_model)
        return self.get_by_key(self.key)

    def get_functions(self) -> list[Function]:
        return [Function(function) for function in db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.virtual_contains_edges,
            direction="outbound",
            filter_by_type="function"
        )]

    def get_classes(self) -> list[Class]:
        return [Class(class_) for class_ in db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.virtual_contains_edges,
            direction="outbound",
            filter_by_type="class"
        )]

    def get_packages(self) -> list[Package]:
        return [Package(package) for package in db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.virtual_contains_edges,
            direction="outbound",
            filter_by_type="package"
        )]

    def get_descendant_tree(self) -> Dict[str, Any]:
        pass