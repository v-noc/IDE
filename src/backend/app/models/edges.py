from .base import BaseEdge
from .node import NodePosition
from pydantic import Field

class BelongsToEdge(BaseEdge):
    """Links a node to a project."""
    edge_type: str = "belongs_to"

class ContainsEdge(BaseEdge):
    """Represents that a node is contained within another (e.g., file in a folder)."""
    edge_type: str = "contains"
    position: NodePosition = Field(..., description="The position of the contained node.")

class CallEdge(BaseEdge):
    """Represents a call from one node to another (e.g., function call)."""
    edge_type: str = "calls"
    position: NodePosition = Field(..., description="The position of the call in the source code.")

class UsesImportEdge(BaseEdge):
    """
    Represents the usage of an import, linking the consumer (a function or class)
    to the provider (another function, class, or an external package).
    """
    edge_type: str = "uses_import"
    target_symbol: str = Field(..., description="The specific symbol being imported (e.g., 'Request').")
    alias: str | None = Field(None, description="The alias used for the import (e.g., 'np').")
    import_position: NodePosition = Field(..., description="The position of the 'import' statement.")
    usage_positions: list[NodePosition] = Field(default_factory=list, description="A list of all positions where the import is used.")

class ImplementsEdge(BaseEdge):
    """Links a class to one of its methods (a function)."""
    edge_type: str = "implements"
