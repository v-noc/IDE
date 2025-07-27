"""
Domain objects for code elements like Functions and Classes.
"""
from __future__ import annotations
from typing import Union, TYPE_CHECKING
from .base import DomainObject
from .package import Package

from ..models import node, edges
from ..db import collections as db

if TYPE_CHECKING:
    from .file import File


class Function(DomainObject[node.FunctionNode]):
    """A domain object representing a function."""
    @property
    def inputs(self) -> list[dict]:
        """Returns the list of input parameters."""
        return self.model.properties.inputs
    
    @property
    def outputs(self) -> list[dict]:
        """Returns the list of output parameters."""
        return self.model.properties.outputs
    
    @property
    def name(self) -> str:
        """Returns the name of the function."""
        return self.model.name
    
    @property
    def qname(self) -> str:
        """Returns the qualified name of the function."""
        return self.model.qname
    
    def add_call(
        self, target: Union['Function', 'Class'], position: node.NodePosition
    ):
        """Creates a 'calls' edge from this function to a target element."""
        if not isinstance(target, (Function, Class)):
            raise TypeError(
                "Call target must be a Function or Class domain object."
            )
            
        call_edge_model = edges.CallEdge(
            _from=self.id,
            _to=target.id,
            position=position
        )
        db.calls_edges.create(call_edge_model)

    def get_parent_file(self) -> 'File':
        """Returns the parent file of the function by finding contains edge."""
        from .file import File
        # Find the contains edge where this function is the target
        contains_edge = db.contains_edges.find_one({'to_id': self.id})
        
        # Debug: Save all contains edges to file
        # all_contains_edges = db.contains_edges.find({})
        # with open('contains_edges.json', 'w') as f:
        #     edge_data = [edge.model_dump() for edge in all_contains_edges]
        #     json.dump(edge_data, f, indent=2)

        if not contains_edge:
            raise ValueError(f"No parent file found for function {self.id}")
        
        # Get the file node that contains this function
        file_node = db.nodes.get(contains_edge.from_id)
        if not file_node:
            raise ValueError(f"File node {contains_edge.from_id} not found")
        
        return File(file_node)
    
    def get_imports(self) -> list[edges.UsesImportEdge]:
        """Returns all import edges from this function."""
        return db.uses_import_edges.find({'from_id': self.id})
    
    def get_nodes_that_import_this(self) -> list['Function']:
        """Returns all nodes that import this function."""
        import_edges = db.uses_import_edges.find({'to_id': self.id})
        result = []
        for edge in import_edges:
            node = db.nodes.get(edge.from_id)
            if node and node.node_type == 'function':
                result.append(Function(node))
        return result
    
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
            target_qname=target.qname,
            alias=alias,
            import_position=import_position,
            usage_positions=usage_positions
        )
        db.uses_import_edges.create(import_edge)

    def add_input(self, name: str, position: node.NodePosition, **kwargs):
        """Adds an input parameter to the function's properties."""
        self.model.properties.inputs.append({
            "name": name, "position": position, **kwargs
        })
        db.nodes.update(self.model)

    def add_output(self, name: str, position: node.NodePosition, **kwargs):
        """Adds an output/return value to the function's properties."""
        self.model.properties.outputs.append({
            "name": name, "position": position, **kwargs
        })
        db.nodes.update(self.model)

    
class Class(DomainObject[node.ClassNode]):
    """A domain object representing a class."""
    @property
    def name(self) -> str:
        """Returns the name of the class."""
        return self.model.name
    
    @property
    def qname(self) -> str:
        """Returns the qualified name of the class."""
        return self.model.qname
    
    def get_parent_file(self) -> 'File':
        """Returns the parent file of the class by finding contains edge."""
        from .file import File
        # Find the contains edge where this class is the target
        contains_edge = db.contains_edges.find_one({'to_id': self.id})
        if not contains_edge:
            raise ValueError(f"No parent file found for class {self.id}")
        
        # Get the file node that contains this class
        file_node = db.file_nodes.get(contains_edge.from_id)
        if not file_node:
            raise ValueError(f"File node {contains_edge.from_id} not found")
        
        return File(file_node)
    
    def get_imports(self) -> list[edges.UsesImportEdge]:
        """Returns all import edges from this class."""
        return db.uses_import_edges.find({'from_id': self.id})
    
    def get_nodes_that_import_this(self) -> list[Union['Function', 'Class']]:
        """Returns all nodes that import this class."""
        import_edges = db.uses_import_edges.find({'to_id': self.id})
        result = []
        for edge in import_edges:
            node = db.nodes.get(edge.from_id)
            if node:
                if node.node_type == 'function':
                    result.append(Function(node))
                elif node.node_type == 'class':
                    result.append(Class(node))
        return result
    
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
            target_qname=target.qname,
            alias=alias,
            import_position=import_position,
            usage_positions=usage_positions
        )
        db.uses_import_edges.create(import_edge)

    def add_field(self, name: str, position: node.NodePosition, **kwargs):
        """Adds a field to the class's properties."""
        self.model.properties.fields.append({"name": name, "position": position, **kwargs})
        db.nodes.update(self.model)
