import datetime
from .base import BaseNode
from .properties import CodePosition, ThemeConfig
from typing import List, Optional, Literal
from pydantic import Field


class ContainerNode(BaseNode):
    node_type: str = "container"
    theme_config: Optional[ThemeConfig] = Field(
        default=None, description="Container theme configuration."
    )
    icon: Optional[str] = Field(default=None, description="Container icon.")
    current_version: int = Field(default=0,
                                 description="The current version of the node.")

    documents: List[str] = Field(
        default_factory=list, description="Documents held by the container."
    )

    # Soft delete fields
    status: Literal["active", "orphaned", "deleted"] = Field(
        default="active",
        description="Node lifecycle status"
    )
    # status_changed_at: Optional[datetime] = Field(
    #     default=None,
    #     description="When status last changed"
    # )
    orphan_reason: Optional[str] = Field(
        default=None,
        description="Why node became orphaned"
    )


class GroupNode(ContainerNode):
    node_type: Literal["group"] = "group"
    group_type: Literal[
        "call",  # call group
        "code",  # function/ class,
        "empty",
        "folder_file",  # folder/ file
    ] = Field(description="The type of group.", default="empty")


class FunctionNode(ContainerNode):
    node_type: Literal["function"] = "function"
    position: CodePosition = Field(..., description="Function position.")


class ClassNode(ContainerNode):
    node_type: Literal["class"] = "class"
    implements: List[str] = Field(
        default_factory=list, description="Class implements.")
    position: CodePosition = Field(..., description="Function position")


class CallNode(ContainerNode):
    node_type: Literal["call"] = "call"
    position: CodePosition = Field(..., description="Function position")
    manually_created: bool = Field(
        default=False, description="Whether the call was manually created."
    )


class FileNode(ContainerNode):
    node_type: Literal["file"] = "file"
    path: str = Field(..., description="File path.")
    hash: str = Field(..., description="File hash.")


class FolderNode(ContainerNode):
    node_type: Literal["folder"] = "folder"
    path: str = Field(..., description="Folder path.")


class ProjectNode(ContainerNode):
    node_type: Literal["project"] = "project"
    path: str = Field(..., description="Folder path")
