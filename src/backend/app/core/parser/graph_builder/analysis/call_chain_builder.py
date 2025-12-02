"""
CallChainBuilder - Recursively constructs call graphs by resolving and traversing function calls.

This module:
1. Resolves calls using CallResolver
2. Checks if resolved callees are local/registered functions
3. Recursively processes function bodies to build complete call chains
4. Handles class instantiation edge case (links to class, processes __init__ if present)
"""

import logging
from pathlib import Path
from typing import List, Optional

from app.core.parser.ast.models import BaseNode, CallNode, ClassNode, FunctionNode
from app.core.parser.ast.scanner import scan
from app.core.parser.jedi_adapter.call_resolver import (
    CallResolutionResult,
    CallResolver,
)
from app.core.parser.jedi_adapter.manager import JediProjectManager
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import CallSiteModel, ScopeModel

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
        max_depth: int = 50,
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
        depth: int = 0,
        parent_context: Optional[object] = None,
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
            parent_context: Optional Jedi context from the caller

        Returns:
            The ID of the created call site
        """
        # Get the source code for this file
        file_path = Path(caller_scope.file_path)
        if not file_path.is_absolute():
            file_path = self.project_path / file_path

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
        except OSError as e:
            logger.error(f"Could not read file {file_path}: {e}")
            return None

        # Resolve the call using Jedi with context preservation
        resolution = self.call_resolver.resolve_call(
            str(file_path),
            source,
            call_node.position.line,
            call_node.position.column,
            call_trailer_index=getattr(call_node, "call_index", None),
            parent_context=parent_context,
        )

        # Determine callee_id based on resolution
        callee_scope = None

        if resolution and resolution.callee_qname:
            jedi_qname = resolution.callee_qname
            candidates = self._candidate_qnames(caller_scope, jedi_qname)

            for full_qname in candidates:
                callee_scope = self.scope_manager.get_scope_by_qname(full_qname)
                if not callee_scope:
                    continue

                if resolution.is_class_instantiation:
                    logger.debug(
                        f"Resolved class instantiation {call_node.name} -> "
                        f"{full_qname} (scope_id={callee_scope.id})"
                    )
                else:
                    logger.debug(
                        f"Resolved call {call_node.name} -> "
                        f"{full_qname} (scope_id={callee_scope.id})"
                    )
                break
            else:
                logger.debug(
                    f"Callee not registered locally for {call_node.name} "
                    f"(Jedi qname candidates: {candidates})"
                )
        else:
            logger.debug(
                f"Could not resolve call {call_node.name} at "
                f"{call_node.position.line}:{call_node.position.column}"
            )
            return
        call_name = self._normalize_call_name(call_node.name)

        # Create the call site
        call_site = self.scope_manager.create_call(
            caller_id=caller_scope.id,
            line=call_node.position.line,
            col=call_node.position.column,
            name=call_name,
            callee_id=callee_scope.id,
            prev_call_site_id=current_call_id,
        )

        # Extract execution context for recursion
        execution_context = resolution.execution_context if resolution else None

        self._process_scope_body(
            callee_scope, depth + 1, call_site.id, execution_context
        )

        return call_site.id

    def _candidate_qnames(
        self,
        caller_scope: ScopeModel,
        jedi_qname: str,
    ) -> List[str]:
        """
        Generate possible fully-qualified qnames for a callee based on the caller scope.

        Jedi often returns module-relative names. This method tries:
        1. The raw qname (if already project-qualified)
        2. Project + module + qname (same file/module reference)
        3. Project + qname (cross-module references within the project)
        """
        if not jedi_qname:
            return []

        normalized = jedi_qname.strip().strip(".")
        if not normalized:
            return []

        scope_parts = caller_scope.qname.split(".")
        project_prefix = scope_parts[0] if scope_parts else self.project_name
        module_prefix = scope_parts[1] if len(scope_parts) >= 2 else None

        candidates: List[str] = []

        if normalized.startswith(f"{project_prefix}."):
            candidates.append(normalized)

        if module_prefix and not normalized.startswith(f"{module_prefix}."):
            candidates.append(f"{project_prefix}.{module_prefix}.{normalized}")

        candidates.append(f"{project_prefix}.{normalized}")

        # Deduplicate while preserving order
        seen = set()
        ordered = []
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                ordered.append(candidate)
        return ordered

    def _normalize_call_name(self, raw_name: Optional[str]) -> Optional[str]:
        """Normalize the call site name for comparisons (use last attribute segment)."""
        if not raw_name:
            return raw_name

        segment = raw_name.strip().split(".")[-1]
        if segment.endswith("()"):
            segment = segment[:-2]

        segment = segment.strip()
        return segment or raw_name

    def _process_scope_body(
        self,
        scope: ScopeModel,
        depth: int,
        current_call_id,
        parent_context: Optional[object] = None,
    ):
        """
        Process all calls within a function/method scope.

        Args:
            scope: The scope to process
            depth: Current recursion depth
            current_call_id: ID of the previous call
            parent_context: Optional Jedi context to use for resolution within this body
        """
        logger.debug(f"Processing body of {scope.qname}")

        # Get the source code
        file_path = Path(scope.file_path)
        if not file_path.is_absolute():
            file_path = self.project_path / file_path

        try:
            with open(file_path, "r", encoding="utf-8") as f:
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

        for call_node in call_nodes:
            current_call_id = self.build_chain(
                call_node, scope, current_call_id, depth, parent_context=parent_context
            )

    def _find_scope_node(
        self, nodes: List[BaseNode], scope: ScopeModel
    ) -> Optional[BaseNode]:
        """
        Find the AST node that corresponds to a scope.

        Matches based on qname or position.
        """
        for node in nodes:
            # Check if this node matches the scope
            if isinstance(node, (FunctionNode, ClassNode)):
                # Match by position (line)
                if node.position.line == scope.start_line and node.name == scope.name:
                    return node

            # Recurse into children
            if hasattr(node, "children"):
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

        if hasattr(node, "children"):
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
