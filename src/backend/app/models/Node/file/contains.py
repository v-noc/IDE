from backend.app.models.Node.base import NodePosition
from backend.app.models.base import BaseEdge

# this is a node that represents a contains edge between a file and schema or function
class ContainsNode(BaseEdge):
    position: NodePosition
    description: str