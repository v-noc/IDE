# src/backend/app/core/parser/python/ast_cache.py
import ast
from typing import Dict

class ASTCache:
    """
    A simple in-memory cache for storing the Abstract Syntax Trees (ASTs)
    of files to avoid re-reading and re-parsing them between analysis passes.
    """
    def __init__(self):
        self._file_asts: Dict[str, ast.Module] = {}

    def get(self, file_path: str) -> ast.Module | None:
        return self._file_asts.get(file_path)

    def set(self, file_path: str, ast_tree: ast.Module) -> None:
        self._file_asts[file_path] = ast_tree
