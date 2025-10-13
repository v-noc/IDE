

from typing import List, Optional, Union
from pydantic import Field

from app.core.model.nodes import CallNode, ClassNode, FunctionNode, FileNode, FolderNode, ProjectNode


class CallTreeNode(CallNode):
    children: List["CallTreeNode"] = Field(
        default_factory=list, description="Call children.")
    target: Optional["ClassTreeNode | FunctionTreeNode"] = None


class ClassTreeNode(ClassNode):
    children: List["ClassTreeNode | FunctionTreeNode | CallTreeNode"] = Field(
        default_factory=list, description="Class children.")


class FunctionTreeNode(FunctionNode):
    children: List["FunctionTreeNode | ClassTreeNode | CallTreeNode"] = Field(
        default_factory=list, description="Function children.")


class FileTreeNode(FileNode):
    hash: Optional[str] = Field(
        default=None,
        description="File hash."
    )
    children: List["ClassTreeNode | FunctionTreeNode | CallTreeNode"] = Field(
        default_factory=list, description="File children.")


class FolderTreeNode(FolderNode):
    children: List["FolderTreeNode | FileTreeNode"] = Field(
        default_factory=list, description="Folder children.")


class ProjectTreeNode(ProjectNode):
    children: List["FolderTreeNode | FileTreeNode"] = Field(
        default_factory=list, description="Project children.")


# A Union of all possible nodes in our tree response
AnyTreeNode = Union[
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
