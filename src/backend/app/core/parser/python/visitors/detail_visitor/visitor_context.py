# src/backend/app/core/parser/python/visitors/detail_visitor/visitor_context.py
import ast
from ...symbol_table import SymbolTable

class VisitorContext:
    """
    A data class to hold and share state between visitors in the pipeline.
    """
    def __init__(self, file_id: str, ast_tree: ast.Module, symbol_table: SymbolTable):
        self.file_id = file_id
        self.ast = ast_tree
        self.symbol_table = symbol_table
        self.results = [] # The final output of the pipeline
