from .base import BaseEdge
from .node import NodePosition
from pydantic import Field

class BelongsToEdge(BaseEdge):
    """Links a node to a project."""
    pass

class ContainsEdge(BaseEdge):
    """Represents that a node is contained within another (e.g., file in a folder)."""
    position: NodePosition = Field(..., description="The position of the contained node.")

class CallEdge(BaseEdge):
    """Represents a call from one node to another (e.g., function call)."""
    position: NodePosition = Field(..., description="The position of the call in the source code.")

class ImportEdge(BaseEdge):
    """Represents an import statement."""
    alias: str | None = None
    position: NodePosition = Field(..., description="The position of the import statement.")
