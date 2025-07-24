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
        # TODO: Implement the logic to record a function declaration.
        # Remember not to call generic_visit() for top-level functions.
        pass

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Identifies a class definition."""
        # TODO: Implement the logic to record a class declaration.
        # Remember to call generic_visit() to find nested methods.
        pass

    def visit_Import(self, node: ast.Import) -> None:
        """Identifies an 'import ...' statement."""
        # TODO: Implement the logic to record an import.
        pass

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Identifies a 'from ... import ...' statement."""
        # TODO: Implement the logic to record a from-import.
        pass
