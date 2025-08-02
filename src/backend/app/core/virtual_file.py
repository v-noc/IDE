from .base import DomainObject
from .file import File
from ..models import node
from ..db import collections as db
from typing import Dict, Any
from .code_elements import Function, Class, Package


class VirtualFile(DomainObject[node.VirtualFileNode]):
    """
    A domain object representing a virtual file.
    """
    @property
    def name(self) -> str:
        return self.model.name

    @property
    def qname(self) -> str:
        return self.model.qname

    @property
    def description(self) -> str | None:
        return self.model.description


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