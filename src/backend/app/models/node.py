from enum import Enum
from pydantic import Field, BaseModel, validator
from typing import Any, Dict, Union
from .base import BaseDocument
from .properties import (
    ProjectProperties,
    FolderProperties,
    FileProperties,
    FunctionProperties,
    ClassProperties,
    ImportProperties,
)

class NodeType(str, Enum):
    PROJECT = "project"
    FOLDER = "folder"
    FILE = "file"
    FUNCTION = "function"
    CLASS = "class"
    IMPORT = "import"

class NodePosition(BaseModel):
    line_no: int
    col_offset: int
    end_line_no: int
    end_col_offset: int

# A Union of all possible properties models
NodeProperties = Union[
    ProjectProperties,
    FolderProperties,
    FileProperties,
    FunctionProperties,
    ClassProperties,
    ImportProperties,
]

# A map from NodeType to the corresponding properties model
NODE_TYPE_MAP = {
    NodeType.PROJECT: ProjectProperties,
    NodeType.FOLDER: FolderProperties,
    NodeType.FILE: FileProperties,
    NodeType.FUNCTION: FunctionProperties,
    NodeType.CLASS: ClassProperties,
    NodeType.IMPORT: ImportProperties,
}

class Node(BaseDocument):
    node_type: NodeType = Field(..., description="The type of the node.")
    name: str = Field(..., description="The name of the node (e.g., function name, file name).")
    qname: str = Field(..., description="The fully qualified name of the node.")
    properties: NodeProperties = Field(..., description="A dictionary of properties specific to the node type.")

    @validator("properties", pre=True, always=True)
    def validate_properties_from_type(cls, v, values):
        """
        Validates the 'properties' field against the correct Pydantic model
        based on the 'node_type' field.
        """
        node_type = values.get("node_type")
        if not node_type:
            raise ValueError("'node_type' must be present to validate 'properties'")

        model = NODE_TYPE_MAP.get(node_type)
        if not model:
            raise ValueError(f"No properties model found for node_type: {node_type}")

        if not isinstance(v, dict):
             raise TypeError("properties must be a dictionary")

        return model(**v)
