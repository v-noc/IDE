

from typing import List, Optional, Union
from pydantic import Field

from app.core.model.nodes import CallNode, ClassNode, FunctionNode, FileNode, FolderNode, ProjectNode, BaseGroupNode


class CallTreeNode(CallNode):
    node_type: str = Field(default="call", description="The type of the node.")
    status: Optional[str] = Field(
        default="unchanged", description="The status of the node.")
    children: List["CallTreeNode | GroupTreeNode"] = Field(
        default_factory=list, description="Call children.")
    target: Optional["ClassTreeNode | FunctionTreeNode"] = None


class ClassTreeNode(ClassNode):
    node_type: str = Field(
        default="class", description="The type of the node.")
    status: Optional[str] = Field(
        default="unchanged", description="The status of the node.")
    children: List["ClassTreeNode | FunctionTreeNode | CallTreeNode | GroupTreeNode"] = Field(
        default_factory=list, description="Class children.")


class FunctionTreeNode(FunctionNode):
    node_type: str = Field(
        default="function", description="The type of the node.")
    status: Optional[str] = Field(
        default="unchanged", description="The status of the node.")
    children: List["FunctionTreeNode | ClassTreeNode | CallTreeNode | GroupTreeNode"] = Field(
        default_factory=list, description="Function children.")


class FileTreeNode(FileNode):
    node_type: str = Field(default="file", description="The type of the node.")
    status: Optional[str] = Field(
        default="unchanged", description="The status of the node.")
    hash: Optional[str] = Field(
        default=None,
        description="File hash."
    )
    children: List["ClassTreeNode | FunctionTreeNode | CallTreeNode | GroupTreeNode"] = Field(
        default_factory=list, description="File children.")


class FolderTreeNode(FolderNode):
    node_type: str = Field(
        default="folder", description="The type of the node.")
    status: Optional[str] = Field(
        default="unchanged", description="The status of the node.")
    children: List["FolderTreeNode | FileTreeNode | GroupTreeNode"] = Field(
        default_factory=list, description="Folder children.")


class ProjectTreeNode(ProjectNode):
    status: Optional[str] = Field(
        default="unchanged", description="The status of the node.")
    version: Optional[str] = Field(
        default=None, description="The version of the project.")

    children: List["FolderTreeNode | FileTreeNode | GroupTreeNode"] = Field(
        default_factory=list, description="Project children.")


class GroupTreeNode(BaseGroupNode):
    node_type: str = Field(
        default="group", description="The type of the node.")
    status: Optional[str] = Field(
        default="unchanged", description="The status of the node.")
    group_type: str = Field(
        default="empty", description="The type of the group.")
    children: List[
        "GroupTreeNode | FolderTreeNode | FileTreeNode | ClassTreeNode | FunctionTreeNode | CallTreeNode"
    ] = Field(default_factory=list, description="Group children.")


# A Union of all possible nodes in our tree response
AnyTreeNode = Union[
    GroupTreeNode,
    FolderTreeNode,
    ProjectTreeNode,
    FileTreeNode,
    ClassTreeNode,
    FunctionTreeNode,
    CallTreeNode,
]

# This is a Pydantic V2 feature to update forward references
CallTreeNode.model_rebuild()
FolderTreeNode.model_rebuild()
ProjectTreeNode.model_rebuild()
FileTreeNode.model_rebuild()
ClassTreeNode.model_rebuild()
FunctionTreeNode.model_rebuild()
GroupTreeNode.model_rebuild()
