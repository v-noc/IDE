"""
CallChainBuilder - Recursively constructs call graphs by resolving and traversing function calls.

This module:
1. Resolves calls using CallResolver
2. Checks if resolved callees are local/registered functions
3. Recursively processes function bodies to build complete call chains
4. Handles class instantiation edge case (links to class, processes __init__ if present)
"""
import logging
from typing import Optional, List
from pathlib import Path

from app.core.parser.ast.models import BaseNode, CallNode, FunctionNode, ClassNode
from app.core.parser.ast.scanner import scan
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeModel, CallSiteModel
from app.core.parser.jedi_adapter.call_resolver import CallResolver, CallResolutionResult
from app.core.parser.jedi_adapter.manager import JediProjectManager

logger = logging.getLogger(__name__)


class CallChainBuilder:
    """
    Builds call chains by recursively resolving and processing function calls.

    This class integrates with CallResolver to:
    - Resolve what function is being called
    - Check if it's a local (registered) function
    - Recursively process the callee's body for nested calls
    - Build a complete call graph chain
    """

    def __init__(
        self,
        project_path: Path,
        project_name: str,
        scope_manager: ScopeManager,
        jedi_manager: JediProjectManager,
        max_depth: int = 50
    ):
        self.project_path = project_path
        self.project_name = project_name
        self.scope_manager = scope_manager
        self.jedi_manager = jedi_manager
        self.call_resolver = CallResolver(jedi_manager)
        self.max_depth = max_depth

        # Track visited scopes to prevent infinite recursion
        self._visited_scopes = set()

    def build_chain(
        self,
        call_node: CallNode,
        caller_scope: ScopeModel,
        current_call_id: Optional[str] = None,
        depth: int = 0
    ) -> Optional[str]:
        """
        Build a call chain starting from a call node.

        This method:
        1. Uses Jedi to resolve the call WITH context preservation  
        2. Creates a call site linking caller -> callee
        3. Returns the call site ID for chaining

        Note: Does NOT recursively process callee bodies - BodyParser handles that
              during its traversal of the AST.

        Args:
            call_node: The AST CallNode to resolve
            caller_scope: The scope containing this call
            current_call_id: ID of the previous call site in the chain
            depth: Current recursion depth (unused, kept for compatibility)

        Returns:
            The ID of the created call site
        """
        # Get the source code for this file
        file_path = Path(caller_scope.file_path)
        if not file_path.is_absolute():
            file_path = self.project_path / file_path

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
        except OSError as e:
            logger.error(f"Could not read file {file_path}: {e}")
            return None

        # Resolve the call using Jedi with context preservation
        resolution = self.call_resolver.resolve_call(
            str(file_path),
            source,
            call_node.position.line,
            call_node.position.column
        )

        # Determine callee_id based on resolution
        callee_id = None

        if resolution and resolution.callee_qname:
            # Jedi returns qnames without the project prefix.
            jedi_qname = resolution.callee_qname
            full_qname = self._qualify_qname(caller_scope.qname, jedi_qname)

            # Check if this is a class instantiation
            if resolution.is_class_instantiation:
                # Link to the CLASS scope, not __init__
                callee_scope = self.scope_manager.get_scope_by_qname(
                    full_qname)

                if callee_scope:
                    callee_id = callee_scope.id
                    logger.debug(
                        f"Resolved class instantiation {call_node.name} -> "
                        f"{full_qname} (scope_id={callee_id})"
                    )
                else:
                    logger.debug(
                        f"Class {full_qname} not registered locally (Jedi qname: {jedi_qname})"
                    )
            else:
                # Regular function/method call
                callee_scope = self.scope_manager.get_scope_by_qname(
                    full_qname)

                if callee_scope:
                    callee_id = callee_scope.id
                    logger.debug(
                        f"Resolved call {call_node.name} -> "
                        f"{full_qname} (scope_id={callee_id})"
                    )
                else:
                    logger.debug(
                        f"Function {full_qname} not registered locally (Jedi qname: {jedi_qname})"
                    )
        else:
            logger.debug(
                f"Could not resolve call {call_node.name} at "
                f"{call_node.position.line}:{call_node.position.column}"
            )

        # Create the call site
        call_site = self.scope_manager.create_call(
            caller_id=caller_scope.id,
            line=call_node.position.line,
            col=call_node.position.column,
            name=call_node.name,
            callee_id=callee_id,
            prev_call_site_id=current_call_id
        )

        return call_site.id

    def _qualify_qname(self, caller_qname: str, jedi_qname: str) -> str:
        """
        Convert a Jedi-provided qname (module-relative) into the fully-qualified qname
        used by the scope manager (project.module.qname).
        """
        # Do not duplicate module names if Jedi already included them
        scope_parts = caller_qname.split('.')
        project_prefix = scope_parts[0] if scope_parts else self.project_name
        module_prefix = scope_parts[1] if len(scope_parts) >= 2 else None

        if module_prefix and not jedi_qname.startswith(f"{module_prefix}."):
            qualified = f"{project_prefix}.{module_prefix}.{jedi_qname}"
        else:
            qualified = f"{project_prefix}.{jedi_qname}"

        # Ensure project name is always present
        if not qualified.startswith(f"{project_prefix}."):
            qualified = f"{project_prefix}.{qualified}"

        return qualified

    def _process_scope_body(self, scope: ScopeModel, depth: int):
        """
        Process all calls within a function/method scope.

        Args:
            scope: The scope to process
            depth: Current recursion depth
        """
        logger.debug(f"Processing body of {scope.qname}")

        # Get the source code
        file_path = Path(scope.file_path)
        if not file_path.is_absolute():
            file_path = self.project_path / file_path

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
        except OSError as e:
            logger.error(f"Could not read file {file_path}: {e}")
            return

        # Parse the AST
        try:
            nodes = scan(source, str(file_path))
        except Exception as e:
            logger.error(f"Failed to scan AST for {file_path}: {e}")
            return

        # Find the function/class node that corresponds to this scope
        target_node = self._find_scope_node(nodes, scope)

        if not target_node:
            logger.warning(f"Could not find AST node for scope {scope.qname}")
            return

        # Extract all call nodes from this scope's body
        call_nodes = self._extract_calls(target_node)

        logger.debug(f"Found {len(call_nodes)} call(s) in {scope.qname}")

        # Process each call recursively
        current_call_id = None
        for call_node in call_nodes:
            current_call_id = self.build_chain(
                call_node,
                scope,
                current_call_id,
                depth
            )

    def _find_scope_node(
        self,
        nodes: List[BaseNode],
        scope: ScopeModel
    ) -> Optional[BaseNode]:
        """
        Find the AST node that corresponds to a scope.

        Matches based on qname or position.
        """
        for node in nodes:
            # Check if this node matches the scope
            if isinstance(node, (FunctionNode, ClassNode)):
                # Match by position (line)
                if (node.position.line == scope.start_line and
                        node.name == scope.name):
                    return node

            # Recurse into children
            if hasattr(node, 'children'):
                result = self._find_scope_node(node.children, scope)
                if result:
                    return result

        return None

    def _extract_calls(self, node: BaseNode) -> List[CallNode]:
        """
        Extract all CallNode instances from a node's children.

        Only extracts direct calls, not calls nested in child scopes.
        """
        calls = []

        if hasattr(node, 'children'):
            for child in node.children:
                if isinstance(child, CallNode):
                    calls.append(child)
                elif isinstance(child, (FunctionNode, ClassNode)):
                    # Don't recurse into nested scopes
                    continue
                else:
                    # Recurse into other nodes (If, For, etc.)
                    calls.extend(self._extract_calls(child))

        return calls

    def reset_visited(self):
        """Reset the visited scopes tracker."""
        self._visited_scopes.clear()
