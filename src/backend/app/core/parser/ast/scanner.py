from .ast_comment import parse
from typing import List

from .models import BaseSchema
from .visitor import CodeStructureVisitor


def scan(content: str) -> List[BaseSchema]:
    """
Parses Python code content and returns a hierarchical list of structured
Pydantic nodes representing the code.

Args:
    content: The Python code as a string.

Returns:
    A list of root nodes representing the parsed code structure.
"""
    try:
        ast_tree = parse(content)

        visitor = CodeStructureVisitor()
        visitor.visit(ast_tree)
        return visitor.get_root_nodes()
    except SyntaxError as e:
        # Handle potential parsing errors gracefully
        print(f"Error parsing code: {e}")
        return []
