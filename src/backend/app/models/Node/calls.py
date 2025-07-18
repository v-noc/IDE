from backend.app.models.base import BaseEdge


# this is a node that represents a call to a function or schema from schema or function
# needs to be a edge because it is a call from one node to another
# must contain the posistion to the file and the line number of the call

class CallNode(BaseEdge):
    description: str
   
