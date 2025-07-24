import ast

from .visitor_context import VisitorContext

class DependencyVisitor(ast.NodeVisitor):
    """
    A visitor to resolve all import statements and create dependency edges.
    """
    def __init__(self, context: VisitorContext):
        self.context = context

    # TODO: Implement visit methods for Name, Attribute, etc. to find import usages.
