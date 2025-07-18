from typing import Any, Dict, List

from backend.app.models.Node.base import Node


class SchemaNode(Node):
    fields: List[Dict[str, Any]]