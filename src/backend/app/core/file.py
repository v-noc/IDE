"""
The File domain object.
"""
from typing import List
from .base import DomainObject
from .code_elements import Function, Class
from ..models import node, edges, properties
from ..db import collections as db


class File(DomainObject[node.FileNode]):
    """
    A domain object representing a file, which contains code elements like
    functions, classes, and imports.
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

    def add_function(
        self, name: str, position: node.NodePosition, **kwargs
    ) -> Function:
        """Adds a new function to this file."""
        # Use the file's qname as base and append function name
        file_qname = self.model.qname
        qname = f"{file_qname}.{name}"
        
        # 1. Create the FunctionNode model
        func_props = properties.FunctionProperties(position=position, **kwargs)
        func_node_model = node.FunctionNode(
            name=name,
            qname=qname,
            node_type="function",
            properties=func_props
        )
        created_func_node = db.nodes.create(func_node_model)

        # 2. Create the ContainsEdge
        contains_edge = edges.ContainsEdge(
            _from=self.id,
            _to=created_func_node.id,
            position=position
        )
        db.contains_edges.create(contains_edge)

        # 3. Return the hydrated Function domain object
        return Function(created_func_node)

    def add_class(
        self, name: str, position: node.NodePosition, **kwargs
    ) -> Class:
        """Adds a new class to this file."""
        # Use the file's qname as base and append class name
        file_qname = self.model.qname
        qname = f"{file_qname}.{name}"

        # 1. Create the ClassNode model
        class_props = properties.ClassProperties(position=position, **kwargs)
        class_node_model = node.ClassNode(
            name=name,
            qname=qname,
            node_type="class",
            properties=class_props
        )
        created_class_node = db.nodes.create(class_node_model)

        # 2. Create the ContainsEdge
        contains_edge = edges.ContainsEdge(
            _from=self.id,
            _to=created_class_node.id,
            position=position
        )
        db.contains_edges.create(contains_edge)

        # 3. Return the hydrated Class domain object
        return Class(created_class_node)

    def get_functions(self) -> List[Function]:
        """Retrieves all functions contained within this file."""
        function_nodes = db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.contains_edges,
            direction="outbound",
            filter_by_type="function"
        )
        return [Function(node_model) for node_model in function_nodes]

    def get_classes(self) -> List[Class]:
        """Retrieves all classes contained within this file."""
        class_nodes = db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.contains_edges,
            direction="outbound",
            filter_by_type="class"
        )
        return [Class(node_model) for node_model in class_nodes]