"""
Scans a project directory and parses Python files to extract AST information.
"""
import os
import ast
from typing import List, Dict, Any, Iterator, Tuple
from ..models.node import NodePosition

class ASTScanner(ast.NodeVisitor):
    """
    A visitor class to traverse the Abstract Syntax Tree of a Python file
    and extract information about classes, functions, imports, and calls.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.results: Dict[str, List[Dict[str, Any]]] = {
            "classes": [],
            "functions": [],
            "imports": [],
            "calls": [],
        }

    def _get_position(self, node: ast.AST) -> NodePosition:
        return NodePosition(
            line_no=node.lineno,
            col_offset=node.col_offset,
            end_line_no=getattr(node, 'end_lineno', node.lineno),
            end_col_offset=getattr(node, 'end_col_offset', node.col_offset)
        )

    def visit_ClassDef(self, node: ast.ClassDef):
        self.results["classes"].append({
            "name": node.name,
            "qname": f"{self.file_path}::{node.name}",
            "position": self._get_position(node)
        })
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Could be a method in a class or a standalone function
        qname = f"{self.file_path}::{node.name}"
        self.results["functions"].append({
            "name": node.name,
            "qname": qname,
            "position": self._get_position(node)
        })
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.results["imports"].append({
                "name": alias.name,
                "qname": f"{self.file_path}::import::{alias.name}",
                "alias": alias.asname,
                "position": self._get_position(node)
            })

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or "."
        for alias in node.names:
            self.results["imports"].append({
                "name": f"{module}.{alias.name}",
                "qname": f"{self.file_path}::import::{module}.{alias.name}",
                "alias": alias.asname,
                "position": self._get_position(node)
            })

    def visit_Call(self, node: ast.Call):
        # This is a simplified representation of a call
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            # Could be something like 'os.path.join'
            # A full implementation would trace the attribute back to its source
            name = node.func.attr
        else:
            name = "unknown_call" # Placeholder for more complex calls

        self.results["calls"].append({
            "name": name,
            "qname": f"{self.file_path}::call::{name}@{node.lineno}",
            "position": self._get_position(node)
        })
        self.generic_visit(node)


class ProjectScanner:
    """
    Scans a project directory, yielding information about folders and parsed files.
    """
    def scan(self, project_path: str) -> Iterator[Tuple[str, Dict[str, Any]]]:
        """
        Walks the project path and yields data about found items.
        
        Yields:
            A tuple of (item_type, data), where item_type is
            'folder', 'file', or 'ast'.
        """
        for root, dirs, files in os.walk(project_path):
            # Yield folders
            for d in dirs:
                if d.startswith('.') or d == '__pycache__':
                    continue
                folder_path = os.path.join(root, d)
                yield "folder", {"path": folder_path, "parent": root}

            # Yield files and their AST
            for f in files:
                if f.startswith('.') or not f.endswith('.py'):
                    continue
                file_path = os.path.join(root, f)
                yield "file", {"path": file_path, "parent": root}
                
                try:
                    with open(file_path, "r", encoding="utf-8") as source:
                        tree = ast.parse(source.read(), filename=file_path)
                        scanner = ASTScanner(file_path)
                        scanner.visit(tree)
                        yield "ast", {"path": file_path, "results": scanner.results}
                except Exception as e:
                    # In a real app, log this error
                    print(f"Could not parse {file_path}: {e}")
                    continue
