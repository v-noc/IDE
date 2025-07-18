from backend.app.models.base import BaseEdge


# this is a node that represents a contains edge between a folder and file or folder
class ContainsFilesOrFolder(BaseEdge):
    virtual_name: str
    description: str