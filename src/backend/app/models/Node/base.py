from enum import Enum
from backend.app.models.base import BaseDocument
from pydantic import BaseModel, Field

class NodeType(Enum):
    FUNCTION = "function"
    SCHEMA = "schema"
    FILE = "file"
    FOLDER = "folder"
    IMPORT = "import"


class Node(BaseDocument):
    name: str
    virtual_name: str
    description: str
    type: NodeType
   


class NodePosition(BaseModel):
    line_no:int = Field(default=0,alias="lineno")
    col_offset:int = Field(default=0,alias="col_offset")
    end_line_no:int = Field(default=0,alias="end_lineno")
    end_col_offset:int = Field(default=0,alias="end_col_offset")



