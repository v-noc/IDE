"""
Domain objects for code elements like Functions, Classes, and Imports.
"""
from ..db.service import DatabaseService
from ..models.node import Node, NodePosition
from ..graph.factories import EdgeFactory

class CodeElement:
    """Base class for a piece of code like a function or class."""
    def __init__(self, node_data: Node, db_service: DatabaseService):
        self.node = node_data
        self.db = db_service
        self.edge_factory = EdgeFactory()

    @property
    def id(self):
        return self.node.id

    @property
    def name(self):
        return self.node.name

    @property
    def qname(self):
        return self.node.qname

class Function(CodeElement):
    """A domain object representing a function."""
    
    def add_call(self, target: 'CodeElement', position: NodePosition):
        """Creates a 'calls' edge from this function to a target element."""
        if not isinstance(target, CodeElement):
            raise TypeError("Call target must be another CodeElement.")
            
        call_edge = self.edge_factory.create_call_edge(
            from_doc_id=self.id,
            to_doc_id=target.id,
            position=position
        )
        self.db.calls.create(call_edge.from_doc_id, call_edge.to_doc_id, call_edge)

class Class(CodeElement):
    """A domain object representing a class."""
    
    def add_call(self, target: 'CodeElement', position: NodePosition):
        """Creates a 'calls' edge from this class to a target element."""
        if not isinstance(target, CodeElement):
            raise TypeError("Call target must be another CodeElement.")

        call_edge = self.edge_factory.create_call_edge(
            from_doc_id=self.id,
            to_doc_id=target.id,
            position=position
        )
        self.db.calls.create(call_edge.from_doc_id, call_edge.to_doc_id, call_edge)

class Import(CodeElement):
    """A domain object representing an import statement."""
    pass
