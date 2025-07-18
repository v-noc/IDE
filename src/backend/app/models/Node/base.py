from enum import Enum
from backend.app.models.base import BaseDocument

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
   




