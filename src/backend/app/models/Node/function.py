from typing import Any, Dict

from backend.app.models.Node.base import Node


class FunctionNode(Node):
    code: str
    inputs: list[Dict[str, Any]]
    outputs: list[Dict[str, Any]]