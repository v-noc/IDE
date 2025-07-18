from pydantic import BaseModel, Field
from typing import Optional
from .base import BaseDocument

class Project(BaseDocument):
    """A project that contains a collection of nodes and their relationships."""
    name: str = Field(..., description="The name of the project.", min_length=3, max_length=100)
    description: Optional[str] = Field(None, description="A brief description of the project.", max_length=500)

class NewProject(BaseModel):
    """Model for creating a new project."""
    name: str
    description: Optional[str] = None

class UpdateProject(BaseModel):
    """Model for updating a project."""
    name: Optional[str] = None
    description: Optional[str] = None
