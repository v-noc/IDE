from typing import Any, Dict

from backend.app.models.Node.base import Node, NodePosition

# this is a node that represents a function, its a collection of inputs and outputs
class FunctionNode(Node):
    inputs: list[Dict[str, Any]]
    outputs: list[Dict[str, Any]]
    