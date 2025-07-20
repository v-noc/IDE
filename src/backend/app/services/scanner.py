"""
Scans a project directory and parses Python files to extract AST information.
"""
import os
import ast
from typing import List, Dict, Any, Iterator
from ..models.node import NodePosition

class ASTScanner(ast.NodeVisitor):
    """
    A visitor class to traverse the Abstract Syntax Tree of a Python file
    and extract information about classes, functions, imports, and calls.
    
    The results are stored in a flat list, making them easy for the
    GraphBuilder to process sequentially.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.results: List[Dict[str, Any]] = []
        self._current_class_name: str | None = None

    def _get_position(self, node: ast.AST) -> NodePosition:
        return NodePosition(
            line_no=node.lineno,
            col_offset=node.col_offset,
            end_line_no=getattr(node, 'end_lineno', node.lineno),
            end_col_offset=getattr(node, 'end_col_offset', node.col_offset)
        )

    def visit_ClassDef(self, node: ast.ClassDef):
        self._current_class_name = node.name
        self.results.append({
            "type": "class",
            "name": node.name,
            "qname": f"{self.file_path}::{node.name}",
            "position": self._get_position(node),
            "file_path": self.file_path,
        })
        self.generic_visit(node)
        self._current_class_name = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # If inside a class, it's a method.
        if self._current_class_name:
            qname = f"{self.file_path}::{self._current_class_name}::{node.name}"
            item_type = "method"
        else:
            qname = f"{self.file_path}::{node.name}"
            item_type = "function"
            
        self.results.append({
            "type": item_type,
            "name": node.name,
            "qname": qname,
            "class_qname": f"{self.file_path}::{self._current_class_name}" if self._current_class_name else None,
            "position": self._get_position(node),
            "file_path": self.file_path,
        })
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.results.append({
                "type": "import",
                "target_symbol": alias.name,
                "alias": alias.asname,
                "position": self._get_position(node),
                "file_path": self.file_path,
                "consumer_qname": self.file_path, # Imports are file-level
            })

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or "."
        for alias in node.names:
            self.results.append({
                "type": "import",
                "target_symbol": f"{module}.{alias.name}",
                "alias": alias.asname,
                "position": self._get_position(node),
                "file_path": self.file_path,
                "consumer_qname": self.file_path, # Imports are file-level
            })

    def visit_Call(self, node: ast.Call):
        # Simplified representation of a call
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        else:
            name = "unknown_call"

        self.results.append({
            "type": "call",
            "target_name": name,
            "position": self._get_position(node),
            "file_path": self.file_path,
        })
        self.generic_visit(node)

def scan_project(project_path: str) -> Iterator[Dict[str, Any]]:
    """
    Walks the project path, scans Python files, and yields structured data.
    """
    for root, dirs, files in os.walk(project_path):
        # Yield folders
        for d in dirs:
            if d.startswith('.') or d == '__pycache__':
                continue
            yield {"type": "folder", "path": os.path.join(root, d), "parent_path": root}

        # Yield files and their AST results
        for f in files:
            if f.startswith('.') or not f.endswith('.py'):
                continue
            file_path = os.path.join(root, f)
            yield {"type": "file", "path": file_path, "parent_path": root}
            
            try:
                with open(file_path, "r", encoding="utf-8") as source:
                    tree = ast.parse(source.read(), filename=file_path)
                    scanner = ASTScanner(file_path)
                    scanner.visit(tree)
                    # Yield each found item from the file
                    for item in scanner.results:
                        yield item
            except Exception as e:
                print(f"Could not parse {file_path}: {e}")
                continue
