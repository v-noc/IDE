from backend.app.models.Node.base import Node

# this is a file node, its a leaf node that represents a file in the project
class FileNode(Node):
    path: str
    virtual_name: str
    