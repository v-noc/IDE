from typing import Optional, Union, Literal
from pydantic import Field
from typing_extensions import Annotated
from .shared import NodePosition
from .base import BaseNode
from .properties import (
    ProjectProperties,
    FolderProperties,
    FileProperties,
    FunctionProperties,
    ClassProperties,
    PackageProperties,
)

# ==============================================================================
# Define Node Models with Specific 'node_type' Literals
# ==============================================================================
# By defining a unique literal for 'node_type' in each model, Pydantic's
# Discriminated Union can automatically determine the correct model to use
# when parsing data, eliminating the need for manual validation.
# ==============================================================================


class ProjectNode(BaseNode):
    node_type: Literal["project"] = "project"
    name: str
    qname: str
    description: Optional[str] = None
    properties: ProjectProperties


class FolderNode(BaseNode):
    node_type: Literal["folder"] = "folder"
    name: str
    qname: str
    description: Optional[str] = None
    properties: FolderProperties


class FileNode(BaseNode):
    node_type: Literal["file"] = "file"
    name: str
    qname: str
    description: Optional[str] = None
    properties: FileProperties


class FunctionNode(BaseNode):
    node_type: Literal["function"] = "function"
    name: str
    qname: str
    description: Optional[str] = None
    properties: FunctionProperties


class ClassNode(BaseNode):
    node_type: Literal["class"] = "class"
    name: str
    qname: str
    description: Optional[str] = None
    properties: ClassProperties


class PackageNode(BaseNode):
    node_type: Literal["package"] = "package"
    name: str
    qname: str
    description: Optional[str] = None
    properties: PackageProperties


class VirtualFolderNode(BaseNode):
    node_type: Literal["virtual_folder"] = "virtual_folder"
    name: str
    qname: str
    description: Optional[str] = None
    call_order: Optional[int] = None
    # properties: VirtualFolderProperties


class VirtualFileNode(BaseNode):
    node_type: Literal["virtual_file"] = "virtual_file"
    name: str
    qname: str
    description: Optional[str] = None
    # properties: VirtualFileProperties


# ==============================================================================
# A Discriminated Union of all specific Node models.
# ==============================================================================
# This allows Pydantic to automatically validate incoming data against the
# correct Node model based on the value of the 'node_type' field.
# ==============================================================================
Node = Annotated[
    Union[
        ProjectNode,
        FolderNode,
        FileNode,
        FunctionNode,
        ClassNode,
        PackageNode,
        VirtualFolderNode,
        VirtualFileNode,
    ],
    Field(discriminator="node_type"),
]
