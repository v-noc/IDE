from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from .base import BaseDocument

class Node(BaseDocument):
    """A generic node within a project."""
    project_key: str = Field(..., description="The key of the project this node belongs to.")
    name: str = Field(..., description="The name of the node.", max_length=100)
    node_type: str = Field("generic", description="The type of the node (e.g., 'task', 'server', 'milestone').")
    properties: Dict[str, Any] = Field(default_factory=dict, description="A flexible dictionary for custom node properties.")

class NewNode(BaseModel):
    """Model for creating a new node."""
    name: str
    node_type: Optional[str] = "generic"
    properties: Optional[Dict[str, Any]] = None

class UpdateNode(BaseModel):
    """Model for updating a node."""
    name: Optional[str] = None
    node_type: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
