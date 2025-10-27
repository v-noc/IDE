from ast import parse
from typing import List

from .models import BaseSchema
from .visitor import CodeStructureVisitor
from .pre_processor import DocstringPreProcessor
import libcst as cst


def scan(content: str, file_path: str) -> List[BaseSchema]:
    """
Parses Python code content and returns a hierarchical list of structured
Pydantic nodes representing the code.

Args:
    content: The Python code as a string.

Returns:
    A list of root nodes representing the parsed code structure.
"""
    try:
        module = cst.parse_module(content)
        transformer = DocstringPreProcessor()
        processed_content = module.visit(transformer)

        with open(file_path, "w") as f:
            f.write(processed_content.code)

        ast_tree = parse(processed_content.code)
        try:
            ast_tree._source_lines = content.splitlines()
        except Exception:
            ast_tree._source_lines = []

        visitor = CodeStructureVisitor()
        visitor.visit(ast_tree)
        return visitor.get_root_nodes()
    except SyntaxError as e:
        # Handle potential parsing errors gracefully
        print(f"Error parsing code: {e}")
        return []
