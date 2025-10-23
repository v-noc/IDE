

from .base import BaseNode
from .properties import TypeKeyValuesProperties, CodePosition, ThemeConfig
from typing import List, Optional, Literal
from pydantic import Field, PrivateAttr


class ContainerNode(BaseNode):
    node_type: str = "container"
    theme_config: Optional[ThemeConfig] = Field(
        default=None,
        description="Container theme configuration."
    )
    icon: Optional[str] = Field(
        default=None,
        description="Container icon."
    )

    documents: List[str] = Field(
        default_factory=list,
        description="Documents held by the container."
    )


class FunctionNode(ContainerNode):
    node_type: Literal["function"] = "function"
    position: CodePosition = Field(
        ...,
        description="Function position."
    )


class ClassNode(ContainerNode):
    node_type: Literal["class"] = "class"
    implements: List[str] = Field(
        default_factory=list,
        description="Class implements."
    )
    position: CodePosition = Field(
        ...,
        description="Function position"
    )


class CallNode(ContainerNode):
    node_type: Literal["call"] = "call"
    position: CodePosition = Field(
        ...,
        description="Function position"
    )


class FileNode(ContainerNode):
    node_type: Literal["file"] = "file"
    path: str = Field(
        ...,
        description="File path."
    )
    hash: str = Field(
        ...,
        description="File hash."
    )


class FolderNode(ContainerNode):
    node_type: Literal["folder"] = "folder"
    path: str = Field(
        ...,
        description="Folder path."
    )


class ProjectNode(ContainerNode):
    node_type: Literal["project"] = "project"
    path: str = Field(
        ...,
        description="Folder path"
    )
