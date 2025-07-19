"""
Provides factories for creating ArangoDB node and edge objects.
"""
from ..models.node import Node, NodeType, NodePosition
from ..models.edges import BelongsToEdge, ContainsEdge, CallEdge, ImportEdge
from typing import Any, Dict

class NodeFactory:
    """A factory for creating Node objects."""

    @staticmethod
    def create_node(node_type: NodeType, name: str, qname: str, properties: Dict[str, Any] = None) -> Node:
        """A generic method to create any node."""
        return Node(
            node_type=node_type,
            name=name,
            qname=qname,
            properties=properties or {}
        )

    @staticmethod
    def create_project_node(name: str, path: str) -> Node:
        return NodeFactory.create_node(NodeType.PROJECT, name, qname=name, properties={'path': path})

    @staticmethod
    def create_folder_node(path: str) -> Node:
        name = path.split('/')[-1]
        return NodeFactory.create_node(NodeType.FOLDER, name, qname=path, properties={'path': path})

    @staticmethod
    def create_file_node(path: str) -> Node:
        name = path.split('/')[-1]
        return NodeFactory.create_node(NodeType.FILE, name, qname=path, properties={'path': path})

    @staticmethod
    def create_class_node(name: str, qname: str, position: NodePosition) -> Node:
        return NodeFactory.create_node(NodeType.CLASS, name, qname, properties={'position': position.model_dump()})

    @staticmethod
    def create_function_node(name: str, qname: str, position: NodePosition) -> Node:
        return NodeFactory.create_node(NodeType.FUNCTION, name, qname, properties={'position': position.model_dump()})

    @staticmethod
    def create_import_node(name: str, qname: str, position: NodePosition) -> Node:
        return NodeFactory.create_node(NodeType.IMPORT, name, qname, properties={'position': position.model_dump()})


class EdgeFactory:
    """A factory for creating Edge objects."""

    @staticmethod
    def create_belongs_to_edge(from_doc_id: str, to_doc_id: str) -> BelongsToEdge:
        return BelongsToEdge(from_doc_id=from_doc_id, to_doc_id=to_doc_id)

    @staticmethod
    def create_contains_edge(from_doc_id: str, to_doc_id: str, position: NodePosition) -> ContainsEdge:
        return ContainsEdge(from_doc_id=from_doc_id, to_doc_id=to_doc_id, position=position)

    @staticmethod
    def create_call_edge(from_doc_id: str, to_doc_id: str, position: NodePosition) -> CallEdge:
        return CallEdge(from_doc_id=from_doc_id, to_doc_id=to_doc_id, position=position)

    @staticmethod
    def create_import_edge(from_doc_id: str, to_doc_id: str, position: NodePosition, alias: str = None) -> ImportEdge:
        return ImportEdge(from_doc_id=from_doc_id, to_doc_id=to_doc_id, position=position, alias=alias)
