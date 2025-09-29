
from .base import BaseNode
from .properties import TypeKeyValuesProperties, CodePosition, ThemeConfig
from typing import List, Optional
from pydantic import Field, PrivateAttr


class FunctionNode(BaseNode):
    node_type: str = "function"
    position: CodePosition = Field(
        ...,
        description="Function position."
    )
    theme_config: Optional[ThemeConfig] = Field(
        default=None,
        description="Function theme configuration."
    )


class ClassNode(BaseNode):
    node_type: str = "class"
    implements: List[str] = Field(
        default_factory=list,
        description="Class implements."
    )
    position: CodePosition = Field(
        ...,
        description="Function position"
    )
    theme_config: Optional[ThemeConfig] = Field(
        default=None,
        description="Function theme configuration."
    )


class CallNode(BaseNode):
    node_type: str = "call"
    position: CodePosition = Field(
        ...,
        description="Function position"
    )
    theme_config: Optional[ThemeConfig] = Field(
        default=None,
        description="Function theme configuration."
    )


class FileNode(BaseNode):
    node_type: str = "file"
    path: str = Field(
        ...,
        description="File path."
    )
    theme_config: Optional[ThemeConfig] = Field(
        default=None,
        description="File theme configuration."
    )


class FolderNode(BaseNode):
    node_type: str = "folder"
    path: str = Field(
        ...,
        description="Folder path."
    )
    theme_config: Optional[ThemeConfig] = Field(
        default=None,
        description="Folder theme configuration."
    )


class ProjectNode(BaseNode):
    node_type: str = "project"
    path: str = Field(
        ...,
        description="Folder path"
    )
    theme_config: Optional[ThemeConfig] = Field(
        default=None,
        description="Folder theme configuration."
    )
