"""
Base classes and utilities for domain objects.
"""
from typing import TypeVar, Generic
from ..models.base import BaseNode

T = TypeVar('T', bound=BaseNode)


class DomainObject(Generic[T]):
    """
    Base class for all domain objects, providing shared functionality
    for interacting with the graph database.
    """
    
    def __init__(self, model: T):
        self.model = model
    
    @property
    def id(self) -> str:
        """Returns the database ID of this domain object."""
        return self.model.id

    @property
    def qname(self) -> str:
        """Returns the qualified name of this domain object."""
        return self.model.qname

    def _generate_child_qname(
        self, child_name: str, is_file: bool = False
    ) -> str:
        """
        Generate a qualified name for a child node following the function 
        pattern.
        
        Args:
            child_name: The name of the child (file or folder name)
            is_file: True if this is a file (will strip .py extension)
            
        Returns:
            The qualified name for the child
        """
        # For files, strip the .py extension from the name
        if is_file and child_name.endswith('.py'):
            child_name = child_name[:-3]
        
        # If parent qname is empty (root project) or this is a project,
        # return just the child name (no project prefix)
        is_project = (hasattr(self.model, 'node_type') and
                     self.model.node_type == 'project')
        if not self.qname or is_project:
            return child_name
        
        # Otherwise, append with dot notation
        return f"{self.qname}.{child_name}"
