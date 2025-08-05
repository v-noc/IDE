"""
Domain objects for code elements like Functions and Classes.
"""
from __future__ import annotations
from typing import Union, TYPE_CHECKING, Optional

from app.models.properties import TypeKeyValuesProperties
from .base import DomainObject
from .package import Package

from ..models import node, edges
from ..db import collections as db

if TYPE_CHECKING:
    from .file import File

CodeElement = Union["Function", "Class"]


class Function(DomainObject[node.FunctionNode]):
    """A domain object representing a function."""
    @property
    def key(self) -> str:
        return self.model.key
    
    @property
    def name(self) -> str:
        """Returns the name of the function."""
        return self.model.name
    
    @property
    def qname(self) -> str:
        """Returns the qualified name of the function."""
        return self.model.qname
    
    @property
    def position(self) -> node.NodePosition:
        """Returns the position of the function."""
        return self.model.properties.position
    
    @property
    def inputs(self) -> list[TypeKeyValuesProperties]:
        """Returns the list of input parameters."""
        return self.model.properties.inputs
    
    @property
    def outputs(self) -> list[TypeKeyValuesProperties]:
        """Returns the list of output parameters."""
        return self.model.properties.outputs
    
    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "id": self.id,
            "name": self.name,
            "qname": self.qname,
            "node_type": self.model.node_type,
            "position": self.position,
            "inputs": self.inputs,
            "outputs": self.outputs
        }
    
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
            order=0,
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
    
    def get_nodes_that_import_this(self) -> list[Union['Function', 'Class']]:
        """Returns all nodes that import this function."""
        import_edges = db.uses_import_edges.find({'to_id': self.id})
        result = []
        for edge in import_edges:
            node = db.nodes.get(edge.from_id)
            if node and node.node_type == 'function':
                result.append(Function(node))
            elif node and node.node_type == 'class':
                result.append(Class(node))
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
            raise TypeError(
                "Import target must be a Function, Class, or Package."
            )

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

    def add_input(self, input: TypeKeyValuesProperties):
        """Adds an input parameter to the function's properties."""
        self.model.properties.inputs.append(input)
        db.nodes.update(self.model)

    def add_output(self, output: TypeKeyValuesProperties):
        """Adds an output/return value to the function's properties."""
        self.model.properties.outputs.append(output)
        db.nodes.update(self.model)

    def get_class_calls(self) -> list[Class]:
        """Returns all class calls from this function."""
        return [Class(node) for node in db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.calls_edges,
            direction="outbound",
            filter_by_type="class",
            limit=100
        )]
    
    def get_function_calls(self) -> list[Function]:
        """Returns all function calls from this class."""
        return [Function(node) for node in db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.calls_edges,
            direction="outbound",
            filter_by_type="function",
            limit=100
        )]
    
    def get_package_calls(self) -> list[Package]:
        """Returns all package calls from this function."""
        return [Package(node) for node in db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.calls_edges,
            direction="outbound",
            filter_by_type="package",
            limit=100
        )]

    def get_node_caller_functions(self) -> list[Function]:
        """Returns all nodes that call this function."""
        return [Function(node) for node in db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.calls_edges,
            direction="inbound",
            filter_by_type="function"
        )]
    
    def get_node_caller_classes(self) -> list[Class]:
        """Returns all nodes that call this function."""
        return [Class(node) for node in db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.calls_edges,
            direction="inbound",
            filter_by_type="class"
        )]
    
   
class Class(DomainObject[node.ClassNode]):
    """A domain object representing a class."""

    @property
    def key(self) -> str:
        return self.model.key

    @property
    def name(self) -> str:
        """Returns the name of the class."""
        return self.model.name
    
    @property
    def qname(self) -> str:
        """Returns the qualified name of the class."""
        return self.model.qname
    
    @property
    def fields(self) -> list[TypeKeyValuesProperties]:
        """Returns the list of fields."""
        return self.model.properties.fields
    
    @property
    def position(self) -> node.NodePosition:
        """Returns the position of the class."""
        return self.model.properties.position
    
    @property
    def methods(self) -> list[Function]:
        """Returns the list of methods."""
        return [Function(node) for node in db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.contains_edges,
            direction="outbound",
            filter_by_type="function",
            limit=100
        )]
    
    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "id": self.id,
            "name": self.name,
            "qname": self.qname,
            "node_type": self.model.node_type,
            "position": self.position,
            "fields": self.fields,
            "methods": [method.to_dict() for method in self.methods]
        }
    
    def get_function_calls(self) -> list[Function]:
        """Returns all function calls from this class."""
        return [Function(node) for node in db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.calls_edges,
            direction="outbound",
            filter_by_type="function",
            limit=100
        )]
    
    def get_class_calls(self) -> list[Class]:
        """Returns all class calls from this class."""
        return [Class(node) for node in db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.calls_edges,
            direction="outbound",
            filter_by_type="class",
            limit=100
        )]

    def get_node_caller_functions(self) -> list[Function]:
        """Returns all nodes that call this function."""
        return [Function(node) for node in db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.calls_edges,
            direction="inbound",
            filter_by_type="function",
            limit=100
        )]
    
    def get_node_caller_classes(self) -> list[Class]:
        """Returns all nodes that call this function."""
        return [Class(node) for node in db.nodes.find_related(
            start_node_id=self.id,
            edge_collection=db.calls_edges,
            direction="inbound",
            filter_by_type="class",
            limit=100
        )]
    
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
    
    def add_method(self, function_id: str) -> Function:
        """
        Adds a new method (Function) to this class and links them with an
        'implements' edge.
        """

        contains_edge = edges.ContainsEdge(
            _from=self.id,
            _to=function_id,
            position=node.NodePosition(
                line_no=0,
                col_offset=0,
                end_line_no=0,
                end_col_offset=0
            )
        )
        db.contains_edges.create(contains_edge)
        return Function(db.nodes.get(function_id))

    def add_call(
        self, 
        target: Union['Function', 'Class'], 
        position: node.NodePosition
    ):
        """Creates a 'calls' edge from this class to a target element."""
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
            raise TypeError(
                "Import target must be a Function, Class, or Package."
            )
            
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

    def add_field(self, field: TypeKeyValuesProperties):
        """Adds a field to the class's properties."""
        self.model.properties.fields.append(field)
        db.nodes.update(self.model)


def to_domain_element(
    element_doc: node.CodeNode,
) -> Optional[CodeElement]:
    """Converts a code node document to a domain element."""
    if element_doc.node_type == "function":
        return Function(element_doc)
    if element_doc.node_type == "class":
        return Class(element_doc)
    return None
