from .collections.projects import ProjectCollectionManager
from .collections.nodes import NodeCollectionManager
from .orm import EdgeManager
from ..models.edges import BelongsToEdge, ContainsEdge, CallEdge, ImportEdge

class DatabaseService:
    """
    A central service that provides access to all database collection and edge managers.
    """
    def __init__(self):
        self.projects = ProjectCollectionManager()
        self.nodes = NodeCollectionManager()
        self.belongs_to = EdgeManager("belongs_to", BelongsToEdge)
        self.contains = EdgeManager("contains", ContainsEdge)
        self.calls = EdgeManager("calls", CallEdge)
        self.imports = EdgeManager("imports", ImportEdge)

# A single instance of the service to be used as a dependency
db_service = DatabaseService()
