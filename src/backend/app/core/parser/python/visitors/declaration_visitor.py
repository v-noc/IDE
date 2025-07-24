# src/backend/app/core/parser/python/visitors/declaration_visitor.py
import ast
from typing import List, Union

class DeclarationVisitor(ast.NodeVisitor):
    """
    A visitor that collects all function, class, and import declarations
    from a file's AST in the first pass.
    """
    def __init__(self):
        self.declared_functions: List[ast.FunctionDef] = []
        self.declared_classes: List[ast.ClassDef] = []
        self.imports: List[Union[ast.Import, ast.ImportFrom]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Identifies a function definition."""
        self.declared_functions.append(node)
        # We do not call generic_visit here to avoid traversing into the function body

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Identifies a class definition."""
        self.declared_classes.append(node)
        # We call generic_visit to find nested methods and classes
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Identifies an 'import ...' statement."""
        self.imports.append(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Identifies a 'from ... import ...' statement."""
        self.imports.append(node)
