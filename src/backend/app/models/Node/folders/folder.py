from backend.app.models.Node.base import Node

# this is a node that represents a folder in the project
class FolderNode(Node):
    path: str
    virtual_name: str
    