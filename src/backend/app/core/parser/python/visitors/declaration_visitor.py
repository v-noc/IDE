# src/backend/app/core/parser/python/visitors/declaration_visitor.py
import ast
from typing import List, Union, Tuple

class DeclarationVisitor(ast.NodeVisitor):
    """
    A visitor that collects all function, class, and import declarations
    from a file's AST in the first pass.
    """
    def __init__(self):
        self.declared_functions: List[ast.FunctionDef] = []
        self.declared_classes: List[ast.ClassDef] = []
        self.methods: List[Tuple[ast.FunctionDef, ast.ClassDef]] = []
        self.imports: List[Union[ast.Import, ast.ImportFrom]] = []
        self._class_stack: List[ast.ClassDef] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Identifies a function definition."""
        if self._class_stack:
            # We're inside a class, so this is a method
            parent_class = self._class_stack[-1]
            self.methods.append((node, parent_class))
        else:
            # This is a standalone function
            self.declared_functions.append(node)
        # We do not call generic_visit here to avoid traversing function body

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Identifies a class definition."""
        self.declared_classes.append(node)
        
        # Push this class onto the context stack
        self._class_stack.append(node)
        
        # Visit the class body to find methods and nested classes
        self.generic_visit(node)
        
        # Pop the class from the context stack when done
        self._class_stack.pop()

    def visit_Import(self, node: ast.Import) -> None:
        """Identifies an 'import ...' statement."""
        self.imports.append(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Identifies a 'from ... import ...' statement."""
        self.imports.append(node)
