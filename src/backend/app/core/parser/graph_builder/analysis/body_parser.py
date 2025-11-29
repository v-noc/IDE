import logging
from pathlib import Path
from typing import List, Optional

from app.core.parser.ast.models import BaseNode, CallNode, FunctionNode, ClassNode
from app.core.parser.ast.scanner import scan
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeModel

logger = logging.getLogger(__name__)


class BodyParser:
    def __init__(self, project_path: Path, scope_manager: ScopeManager):
        self.project_path = project_path
        self.manager = scope_manager

    def process_ast(self, file_scope: ScopeModel):
        """
        Phase 2: Analyze the AST tree for calls.
        Traverses the tree, entering scopes (Function/Class) as encountered.
        """
        file_path = Path(file_scope.file_path)
        if not file_path.is_absolute():
            file_path = Path(self.project_path) / file_path

        try:
            with open(file_path, "r", encoding="utf-8") as source:
                content = source.read()
        except OSError as exc:
            logger.error("Failed to read file %s: %s", file_path, exc)
            return

        try:
            nodes = scan(content, str(file_path))
        except Exception as exc:
            logger.error("Failed to re-scan AST for %s: %s", file_path, exc)
            return

        # Start traversal from file scope
        self._traverse(nodes, file_scope)

    def _traverse(self, nodes: List[BaseNode], current_scope: ScopeModel, prev_call_id: Optional[str] = None):
        current_call_id = prev_call_id

        # Clear calls for the current scope before processing (Incremental update)
        # Note: We do this once per scope entry.
        # But _traverse is called recursively.
        # We should clear calls ONLY when we first enter the scope.
        # But here we are iterating nodes IN the scope.
        # The caller (process_ast or _traverse) is responsible for switching scopes.
        # Let's handle clearing in the "Enter Scope" logic.

        # Actually, for the File Scope, we should clear it at the start of process_ast.
        # For child scopes, we clear when we encounter them.

        for node in nodes:
            if isinstance(node, (ClassNode, FunctionNode)):
                # Enter Scope
                # The node.id should have been set by Phase 1 (ASTProcessor)
                if not node.id:
                    logger.warning(
                        f"Node {node.name} has no ID in Phase 2. Skipping.")
                    continue

                child_scope = self.manager.get_scope(node.id)
                if not child_scope:
                    logger.warning(
                        f"Scope not found for node {node.name} ({node.id}). Skipping.")
                    continue

                # Clear old calls for this child scope
                self.manager.clear_calls(child_scope.id)

                # Recurse into child scope
                if hasattr(node, "children"):
                    self._traverse(node.children, child_scope)

            elif isinstance(node, CallNode):
                # Handle Call
                call_site = self.manager.create_call(
                    caller_id=current_scope.id,
                    line=node.position.line,
                    col=node.position.column,
                    name=node.name,
                    callee_id=None,
                    prev_call_site_id=current_call_id
                )
                current_call_id = call_site.id

                # Recurse into arguments (staying in current scope)
                if hasattr(node, "children"):
                    self._traverse(node.children, current_scope,
                                   current_call_id)

            else:
                # Other nodes (If, For, etc.) - Recurse staying in current scope
                if hasattr(node, "children"):
                    self._traverse(node.children, current_scope,
                                   current_call_id)
