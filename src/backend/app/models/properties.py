"""
Pydantic models for the 'properties' field of a Node, based on NodeType.
"""
from pydantic import BaseModel, Field
from typing import List
from .shared import NodePosition


class BaseProperties(BaseModel):
    """A base model for all properties to ensure consistency."""
    pass


class ProjectProperties(BaseProperties):
    path: str = Field(
        ..., 
        description="The absolute path to the project directory."
    )


class FolderProperties(BaseProperties):
    path: str = Field(..., description="The absolute path to the folder.")


class FileProperties(BaseProperties):
    path: str = Field(..., description="The absolute path to the file.")


class TypeKeyValuesProperties(BaseProperties):
    varname: str = Field(
        ..., 
        description="The key of the type key-value pair."
    )
    varType: str = Field(..., description="The type of the variable.")
    position: NodePosition = Field(
        ..., 
        description="The position of the variable."
    )


class FunctionProperties(BaseProperties):
    position: NodePosition
    inputs: List[TypeKeyValuesProperties] = Field(
        default_factory=list, 
        description="Function parameters."
    )
    outputs: List[TypeKeyValuesProperties] = Field(
        default_factory=list, 
        description="Function return types."
    )


class ClassProperties(BaseProperties):
    position: NodePosition
    fields: List[TypeKeyValuesProperties] = Field(
        default_factory=list, 
        description="Class attributes or fields."
    )


class PackageProperties(BaseProperties):
    """Properties for a PackageNode."""
    version: str | None = None
    source: str | None = None  # e.g., "pypi"
    imported_paths: List[str] = Field(
        default_factory=list, 
        description="List of specific imports from this package "
                    "(e.g., ['BaseModel', 'Field'])"
    )

class VirtualFolderProperties(BaseProperties):
    pass


class VirtualFileProperties(BaseProperties):
    pass