from __future__ import annotations
import ast
from typing import List

from .converters import SchemaConverter
from .models import BaseSchema, ParentSchema


class CodeStructureVisitor(ast.NodeVisitor):
    """
    A single-pass AST visitor that builds a hierarchical tree of Pydantic
    models representing the code structure.

    It uses a NodeConverter to handle the translation from ast.AST to BaseNode
    and manages the parent-child relationships using a context stack.
    """

    def __init__(self):
        self.converter = SchemaConverter()
        self.root_nodes: List[BaseSchema] = []
        self._context_stack: List[ParentSchema] = []

    def get_root_nodes(self) -> List[BaseSchema]:
        return self.root_nodes

    def _add_node(self, node: BaseSchema):
        """Adds a node to the tree, linking it to the current parent."""
        if not self._context_stack:
            self.root_nodes.append(node)
        else:
            parent = self._context_stack[-1]
            parent.children.append(node)

    def _visit_and_manage_context(self, pydantic_node: ParentSchema, ast_node: ast.AST):
        """
        Helper to handle the common pattern for context-managing nodes
        (classes, functions).
        """
        self._add_node(pydantic_node)
        self._context_stack.append(pydantic_node)
        self.generic_visit(ast_node)
        self._context_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Pre-scan for return statements to pass to the converter
        returns = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
        pydantic_node = self.converter.convert_functiondef(node, returns)
        self._visit_and_manage_context(pydantic_node, node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        pydantic_node = self.converter.convert_classdef(node)
        self._visit_and_manage_context(pydantic_node, node)

    def visit_Import(self, node: ast.Import) -> None:
        pydantic_node = self.converter.convert_import(node)
        self._add_node(pydantic_node)
        # Do not call generic_visit, as we've handled everything.

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        pydantic_node = self.converter.convert_importfrom(node)
        self._add_node(pydantic_node)
        # Do not call generic_visit.

    def visit_Assign(self, node: ast.Assign) -> None:
        pydantic_node = self.converter.convert_assign(node)
        self._add_node(pydantic_node)
        # We must visit the value side to find nested calls, e.g., x = my_func()
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        pydantic_node = self.converter.convert_annassign(node)
        self._add_node(pydantic_node)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        pydantic_node = self.converter.convert_call(node)
        self._add_node(pydantic_node)

        # Do not call generic_visit to avoid processing children twice.
        # The converter handles recursion into function calls.
