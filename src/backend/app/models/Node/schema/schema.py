from typing import Any, Dict, List

from backend.app.models.Node.base import Node

# this is a node that represents a schema(class / struct), its a collection of fields
class SchemaNode(Node):
    fields: List[Dict[str, Any]]
    virtual_name: str