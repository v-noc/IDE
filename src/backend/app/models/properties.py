"""
Pydantic models for the 'properties' field of a Node, based on NodeType.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from .node import NodePosition

class BaseProperties(BaseModel):
    """A base model for all properties to ensure consistency."""
    pass

class ProjectProperties(BaseProperties):
    path: str = Field(..., description="The absolute path to the project directory.")

class FolderProperties(BaseProperties):
    path: str = Field(..., description="The absolute path to the folder.")

class FileProperties(BaseProperties):
    path: str = Field(..., description="The absolute path to the file.")

class FunctionProperties(BaseProperties):
    position: NodePosition
    inputs: List[Dict[str, Any]] = Field(default_factory=list, description="Function parameters.")
    outputs: List[Dict[str, Any]] = Field(default_factory=list, description="Function return types.")

class ClassProperties(BaseProperties):
    position: NodePosition
    fields: List[Dict[str, Any]] = Field(default_factory=list, description="Class attributes or fields.")
    
class ImportProperties(BaseProperties):
    position: NodePosition
    module: str | None = Field(None, description="The module from which something is imported, if applicable.")
