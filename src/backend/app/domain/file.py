"""
The File domain object.
"""
from .container import Container
from .code_elements import Function, Class, Import
from ..models.node import Node, NodeType, NodePosition
from typing import List

class File(Container):
    """
    A domain object representing a file, which contains code elements like
    functions, classes, and imports.
    """
    def __init__(self, node_data: Node, db_service):
        super().__init__(node=node_data, db_service=db_service)

    @property
    def path(self):
        return self.node.properties.get("path")

    def add_function(self, name: str, position: NodePosition, **kwargs) -> Function:
        """Adds a new function to this file."""
        qname = f"{self.path}::{name}"
        return self._add_element(
            domain_class=Function,
            node_type=NodeType.FUNCTION,
            name=name,
            qname=qname,
            position=position,
            properties={"position": position.model_dump(), **kwargs}
        )

    def add_class(self, name: str, position: NodePosition, **kwargs) -> Class:
        """Adds a new class to this file."""
        qname = f"{self.path}::{name}"
        return self._add_element(
            domain_class=Class,
            node_type=NodeType.CLASS,
            name=name,
            qname=qname,
            position=position,
            properties={"position": position.model_dump(), **kwargs}
        )

    def add_import(self, name: str, position: NodePosition, **kwargs) -> Import:
        """Adds a new import statement to this file."""
        qname = f"{self.path}::import::{name}"
        return self._add_element(
            domain_class=Import,
            node_type=NodeType.IMPORT,
            name=name,
            qname=qname,
            position=position,
            properties={"position": position.model_dump(), **kwargs}
        )

    def get_functions(self) -> List[Function]:
        """Retrieves all functions contained within this file."""
        # This requires a graph traversal query (AQL)
        query = """
        FOR node IN 1..1 OUTBOUND @file_id contains
          FILTER node.node_type == 'function'
          RETURN node
        """
        cursor = self.db.db.aql.execute(query, bind_vars={"file_id": self.node.id})
        return [Function(Node(**doc), self.db) for doc in cursor]
