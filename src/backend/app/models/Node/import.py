from backend.app.models.Node.base import NodePosition
from backend.app.models.base import BaseEdge
from pydantic import BaseModel

class ImportMetadata(BaseModel):
    alias: str
    position: NodePosition

# this is a node that represents an import statement, its an edge between a function and function or schema and file or folder
# must contain the posistion to the file and the line number of the import
class ImportNode(BaseEdge):
    path: str
    name: str
    description: str