from typing import Annotated, Union
from pydantic import Field
from .nodes import FunctionNode, ClassNode, ProjectNode, FolderNode, FileNode, CallNode
from .logs import LogNode

CodeNode = Union[FunctionNode, ClassNode, CallNode]

AllNodes = Annotated[
    Union[

        ProjectNode,
        FolderNode,
        FileNode,
        FunctionNode,  # Included in CodeNode
        ClassNode,    # Included in CodeNode
        CallNode,    # Included in CodeNode
    ],
    Field(discriminator="node_type"),
]
