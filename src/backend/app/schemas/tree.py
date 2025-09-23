

from typing import List, Optional, Union
from pydantic import BaseModel, Field

from orm.models.nodes import CallNode
from orm.models.nodes import ClassNode
from orm.models.nodes import FunctionNode
from orm.models.nodes import FileNode
from orm.models.nodes import FolderNode
from orm.models.nodes import ProjectNode


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
