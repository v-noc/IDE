"""
A base class for domain objects that act as containers.
"""
from ..db.service import DatabaseService
from ..models.node import Node, NodeType, NodePosition
from ..graph.factories import NodeFactory, EdgeFactory
from typing import Type, TypeVar

T = TypeVar('T')

class Container:
    """
    A base class for domain objects that can contain other graph elements,
    such as a Project containing Folders or a File containing Functions.
    
    It encapsulates the logic for creating a new node and linking it with
    a 'contains' edge.
    """
    def __init__(self, node: Node, db_service: DatabaseService):
        if not isinstance(node, Node):
            raise TypeError("Container must be initialized with a valid Node model.")
        self.node = node
        self.db = db_service
        self.node_factory = NodeFactory()
        self.edge_factory = EdgeFactory()

    def _add_element(
        self,
        domain_class: Type[T],
        node_type: NodeType,
        position: NodePosition = None,
        **kwargs
    ) -> T:
        """
        A generic method to add a new element inside this container.

        Args:
            domain_class: The domain class to instantiate (e.g., File, Function).
            node_type: The NodeType of the new element.
            position: The position of the element within its parent (if applicable).
            **kwargs: Properties for the new node (e.g., name, qname).

        Returns:
            An instance of the specified domain_class.
        """
        # Default position if not provided
        if position is None:
            position = NodePosition(line_no=0, col_offset=0, end_line_no=0, end_col_offset=0)

        # 1. Create the new node
        properties = {"position": position.model_dump()} if position else {}
        new_node_model = self.node_factory.create_node(
            node_type=node_type,
            properties=properties,
            **kwargs
        )
        created_node = self.db.nodes.create(new_node_model)

        # 2. Create the 'contains' edge to link it to this container
        from_id = self.node.id # The ID of this container node
        to_id = created_node.id
        contains_edge = self.edge_factory.create_contains_edge(from_id, to_id, position)
        self.db.contains.create(contains_edge.from_doc_id, contains_edge.to_doc_id, contains_edge)

        # 3. Return the hydrated domain object for the new element
        return domain_class(node_data=created_node, db_service=self.db)
