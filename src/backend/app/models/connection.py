from pydantic import BaseModel, Field
from typing import Optional
from .base import BaseEdge

class Connection(BaseEdge):
    """An edge that connects two nodes, representing a relationship."""
    relationship_type: str = Field("related_to", description="The type of relationship (e.g., 'depends_on', 'contains').")

class NewConnection(BaseModel):
    """Model for creating a new connection between nodes."""
    relationship_type: Optional[str] = "related_to"
