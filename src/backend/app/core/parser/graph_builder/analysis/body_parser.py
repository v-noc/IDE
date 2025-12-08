import logging
from pathlib import Path
from typing import List, Optional

from app.core.parser.ast.models import BaseNode, CallNode, ClassNode, FunctionNode
from app.core.parser.ast.scanner import scan
from app.core.parser.graph_builder.analysis.call_chain_builder import CallChainBuilder
from app.core.parser.jedi_adapter.manager import JediProjectManager
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeModel

logger = logging.getLogger(__name__)


class BodyParser:
    def __init__(
        self,
        project_path: Path,
        project_name: str,
        scope_manager: ScopeManager,
        jedi_manager: JediProjectManager,
        batch_size: int = 1000,
    ):
        self.project_path = project_path
        self.project_name = project_name
        self.manager = scope_manager
        self.jedi_manager = jedi_manager
        self.batch_size = batch_size
        self.call_sync_service = None
        self.processed_scope_ids = set()
        # Initialize CallChainBuilder for recursive call resolution
        self.call_chain_builder = CallChainBuilder(
            project_path=project_path,
            project_name=project_name,
            scope_manager=scope_manager,
            jedi_manager=jedi_manager,
        )

    def flush_all_call_sites(self):
        self.call_chain_builder.flush_all_call_sites()
        self.call_sync_service(self.processed_scope_ids)
        self.processed_scope_ids.clear()

    def set_call_sync_service(self, call_sync_service):
        self.call_sync_service = call_sync_service

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
        self.processed_scope_ids.add(file_scope.id)

    def _traverse(
        self,
        nodes: List[BaseNode],
        current_scope: ScopeModel,

    ):
        """
        Traverse AST nodes in the current scope.

        Call chain logic:
        - Root calls (at scope level): prev_call_id = None (independent calls)
        - Nested calls (in arguments): prev_call_id chains them together

        Example:
          func1()          # Root call, prev_call_id=None
          func2(func3())   # func2 is root, func3 chains to func2's call site
        """

        for node in nodes:
            # Auto-flush if buffer exceeds batch size
            if len(self.call_chain_builder._call_site_buffer) >= self.batch_size:
                self.flush_all_call_sites()

            if isinstance(node, (ClassNode, FunctionNode)):
                # Enter child scope (function or class)
                if not node.id:
                    logger.warning(
                        f"Node {node.name} has no ID in Phase 2. Skipping.")
                    continue

                child_scope = self.manager.get_scope(node.id)
                if not child_scope:
                    logger.warning(
                        f"Scope not found for node {node.name} ({node.id}). Skipping."
                    )
                    continue

                # Clear old calls for this scope before processing
                self.manager.clear_calls(child_scope.id)

                # Recurse into the scope to process its calls
                # All calls in child scope are root calls (prev_call_id=None)
                if hasattr(node, "children"):
                    self._traverse(node.children, child_scope)

                self.processed_scope_ids.add(node.id)

            elif isinstance(node, CallNode):
                # Create call site (this is a root call at this scope level)
                logger.debug(
                    f"Processing CallNode: {node.name} at {node.position.line}:{node.position.column} in scope {current_scope.qname}"
                )
                call_site_id = self.call_chain_builder.build_chain(
                    call_node=node,
                    caller_scope=current_scope,
                    current_call_id=None,  # Chain to previous if in nested context
                    depth=0,
                )

                logger.debug(f"Created call site with ID: {call_site_id}")
