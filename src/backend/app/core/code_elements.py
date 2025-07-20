"""
Domain objects for code elements like Functions and Classes.
"""
from __future__ import annotations
from typing import Union
from .base import DomainObject
from .package import Package
from ..models import node, edges
from ..db import collections as db

class Function(DomainObject[node.FunctionNode]):
    """A domain object representing a function."""
    
    def add_call(self, target: Union['Function', 'Class'], position: node.NodePosition):
        """Creates a 'calls' edge from this function to a target element."""
        if not isinstance(target, (Function, Class)):
            raise TypeError("Call target must be a Function or Class domain object.")
            
        call_edge_model = edges.CallEdge(
            _from=self.id,
            _to=target.id,
            position=position
        )
        db.calls_edges.create(call_edge_model)

    def uses_import(
        self,
        target: Union["Function", "Class", "Package"],
        target_symbol: str,
        import_position: node.NodePosition,
        usage_positions: list[node.NodePosition],
        alias: str | None = None
    ):
        """Creates a 'uses_import' edge from this element to its dependency."""
        if not isinstance(target, (Function, Class, Package)):
            raise TypeError("Import target must be a Function, Class, or Package.")

        import_edge = edges.UsesImportEdge(
            _from=self.id,
            _to=target.id,
            target_symbol=target_symbol,
            alias=alias,
            import_position=import_position,
            usage_positions=usage_positions
        )
        db.uses_import_edges.create(import_edge)

class Class(DomainObject[node.ClassNode]):
    """A domain object representing a class."""
    
    def add_method(self, name: str, position: node.NodePosition, **kwargs) -> Function:
        """
        Adds a new method (Function) to this class and links them with an
        'implements' edge.
        """
        qname = f"{self.model.qname}::{name}"
        func_props = node.FunctionProperties(position=position, **kwargs)
        func_node_model = node.FunctionNode(
            name=name,
            qname=qname,
            node_type="function",
            properties=func_props
        )
        created_func_node = db.nodes.create(func_node_model)
        implements_edge = edges.ImplementsEdge(
            _from=self.id,
            _to=created_func_node.id
        )
        db.implements_edges.create(implements_edge)
        return Function(created_func_node)

    def add_call(self, target: Union['Function', 'Class'], position: node.NodePosition):
        """Creates a 'calls' edge from this class to a target element."""
        if not isinstance(target, (Function, Class)):
            raise TypeError("Call target must be a Function or Class domain object.")
        call_edge_model = edges.CallEdge(
            _from=self.id,
            _to=target.id,
            position=position
        )
        db.calls_edges.create(call_edge_model)

    def uses_import(
        self,
        target: Union["Function", "Class", "Package"],
        target_symbol: str,
        import_position: node.NodePosition,
        usage_positions: list[node.NodePosition],
        alias: str | None = None
    ):
        """Creates a 'uses_import' edge from this element to its dependency."""
        if not isinstance(target, (Function, Class, Package)):
            raise TypeError("Import target must be a Function, Class, or Package.")
            
        import_edge = edges.UsesImportEdge(
            _from=self.id,
            _to=target.id,
            target_symbol=target_symbol,
            alias=alias,
            import_position=import_position,
            usage_positions=usage_positions
        )
        db.uses_import_edges.create(import_edge)
