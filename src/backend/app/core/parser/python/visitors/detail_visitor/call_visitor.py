import ast

from .visitor_context import VisitorContext

class CallVisitor(ast.NodeVisitor):
    """
    A visitor to resolve all function/method calls and create CallEdges.
    """
    def __init__(self, context: VisitorContext):
        self.context = context

    def visit_Call(self, node: ast.Call) -> None:
        """Resolves a call target and creates a CallEdge."""
        # TODO: Implement the logic to resolve the call and create an edge.
        pass
