from backend.app.models.Node.base import Node
from backend.app.models.base import BaseDocument

# this is a project node, its a collection of nodes
# it must contain the path to the project
# it must contain the name of the project
# it must contain the description of the project
# it must contain the virtual name of the project
# it must contain the nodes(folders, files, schemas, functions, imports, calls) in the project

class Project(BaseDocument):
    name: str
    description: str
    virtual_name: str
    path: str
    nodes: list[Node]