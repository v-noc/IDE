"""
CallResolver - Resolves function/method calls using Jedi's context-preserving APIs.

This module provides accurate call resolution by:
1. Preserving execution context through the call chain
2. Handling nested attributes (e.g., a.b.c())
3. Properly resolving class instantiation
4. Extracting qualified names from resolved callees
"""
from jedi.api import helpers
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional

import jedi
from jedi.inference.helpers import infer_call_of_leaf
from jedi.inference.syntax_tree import infer_trailer

from .manager import JediProjectManager

logger = logging.getLogger(__name__)


@dataclass
class CallResolutionResult:
    """Result of resolving a call site."""

    callee_qname: Optional[str] = None
    """Fully qualified name of the resolved callee"""

    callee_values: List[Any] = None
    """Jedi values representing the callee"""

    execution_context: Optional[Any] = None
    """Jedi execution context for the call"""

    is_class_instantiation: bool = False
    """True if this is a class instantiation (not a simple function call)"""

    class_qname: Optional[str] = None
    """For class instantiation, the qualified name of the class"""

    def __post_init__(self):
        if self.callee_values is None:
            self.callee_values = []


class CallResolver:
    """
    Resolves function and method calls using Jedi's internal APIs.

    This class uses Jedi's context-preserving mechanisms to accurately
    resolve what function/method is being called, even for complex
    attribute chains like `obj.attr.method()`.
    """

    def __init__(self, jedi_manager: JediProjectManager):
        self.jedi_manager = jedi_manager

    def resolve_call(
        self,
        file_path: str,
        source: str,
        line: int,
        column: int,
        call_trailer_index: Optional[int] = None,
        parent_context: Optional[Any] = None,
    ) -> Optional[CallResolutionResult]:
        """
        Resolve a call at the given position.

        Args:
            file_path: Path to the file
            source: Source code content
            line: Line number (1-indexed)
            column: Column number (0-indexed in Jedi)
            call_trailer_index: Optional index of the call trailer
            parent_context: Optional Jedi context from the caller (for recursion)

        Returns:
            CallResolutionResult if successful, None otherwise
        """
        try:
            script = self.jedi_manager.get_script(file_path, source)

            # Use provided parent context or fall back to module context
            if parent_context:
                context = parent_context
            else:
                context = script._get_module_context()

            # Find the call node at this position
            call_leaf = script._module_node.get_name_of_position(
                (line, column))
            if not call_leaf:
                call_leaf = script._module_node.get_name_of_position(
                    (line, column + 1))
                if not call_leaf:
                    logger.debug(
                        f"No leaf found at {file_path}:{line}:{column}")
                    return None

            # Navigate up to find the atom_expr or power node
            atom_expr = self._find_call_expression(call_leaf)
            if not atom_expr:
                logger.debug(
                    f"Not a call expression at {file_path}:{line}:{column}")
                return None

            # Find the trailer with the call parentheses
            trailer_indices = [
                idx
                for idx, child in enumerate(atom_expr.children)
                if child.type == "trailer"
                and child.children
                and getattr(child.children[0], "value", None) == "("
            ]
            if not trailer_indices:
                logger.debug(
                    f"No call trailers found at {file_path}:{line}:{column}")
                return None

            if call_trailer_index is None or call_trailer_index >= len(trailer_indices):
                trailer_idx = trailer_indices[-1]
            else:
                trailer_idx = trailer_indices[call_trailer_index]

            trailer = atom_expr.children[trailer_idx]
            if trailer.type != "trailer" or trailer.children[0].value != "(":
                logger.debug(
                    f"Last trailer is not a call at {file_path}:{line}:{column}"
                )
                return None

            # Create context for the call site
            # If we have a parent_context, we might need to be careful,
            # but create_context usually takes a node and returns the context for it.
            # However, if we are already in a context, we should use that context's inference state?
            # Actually, module_context.create_context(call_leaf) creates a context *at* that leaf.
            # If we passed parent_context, we want to use it to infer the callee.

            # When we have parent_context (e.g. inside a function), we should use it
            # to infer the values.

            call_context = context.create_context(call_leaf)

            # Infer the callee (everything before the call trailer)

            callee_values = helpers.infer(
                script._inference_state, call_context, call_leaf)

            if not callee_values:
                logger.debug(
                    f"Could not infer callee at {file_path}:{line}:{column}")
                return None

            # Extract qualified names and check for class instantiation
            result = CallResolutionResult(callee_values=list(callee_values))

            for callee in callee_values:
                # Check if this is a class instantiation
                if callee.api_type == "class":
                    result.is_class_instantiation = True
                    result.class_qname = self._extract_qualified_name(callee)
                    result.callee_qname = result.class_qname

                    # For classes, we want to link to the class scope, not __init__
                    # But we may still want to process __init__ body
                    logger.debug(
                        f"Resolved class instantiation: {result.class_qname}")
                else:
                    # Regular function or method call
                    result.callee_qname = self._extract_qualified_name(callee)
                    logger.debug(f"Resolved call to: {result.callee_qname}")

                # Try to create execution context
                # Try to create execution context
                try:
                    # Prepare arguments
                    arglist = trailer.children[1] if len(
                        trailer.children) > 2 else None
                    from jedi.inference.arguments import TreeArguments

                    tree_arguments = TreeArguments(
                        script._inference_state, call_context, arglist, trailer
                    )

                    # Create execution context
                    if callee.api_type == "class":
                        # Classes don't accept arguments for context creation
                        # We get the class context (static), not instance context
                        exec_context = callee.as_context()
                    else:
                        exec_context = callee.as_context(
                            arguments=tree_arguments)

                    result.execution_context = exec_context
                    logger.debug(f"Created execution context: {exec_context}")
                except Exception as e:
                    logger.warning(f"Could not create execution context: {e}")

                # We only need the first successful resolution
                if result.callee_qname:
                    break

            return result if result.callee_qname else None

        except Exception as e:
            logger.error(
                f"Error resolving call at {file_path}:{line}:{column}: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _find_call_expression(self, leaf):
        """Navigate up the AST to find the atom_expr or power node."""
        curr = leaf
        while curr.parent and curr.type not in ("atom_expr", "power"):
            curr = curr.parent

        if curr.type in ("atom_expr", "power"):
            return curr
        return None

    def _infer_callee(self, context, script, atom_expr, trailer_index):
        """
        Infer the callee by applying all trailers except the call trailer.

        This preserves the context through attribute accesses like a.b.c
        """
        base = atom_expr.children[0]
        values = context.infer_node(base)
        if not values:
            module_context = script._get_module_context()
            res = script._inference_state.infer(module_context,
                                                base)
            print(f"res: {res}")
            values = module_context.infer_node(base)

        # Apply all trailers EXCEPT the last one (which is the call)
        for trailer in atom_expr.children[1:trailer_index]:
            values = infer_trailer(context, values, trailer)

        return values

    def _extract_qualified_name(self, value) -> Optional[str]:
        """
        Extract fully qualified name from a Jedi value.

        Returns the most specific name available, always including the module name.
        """
        try:
            # Try to get qualified names from Jedi first (has correct class hierarchy)
            qnames = None
            if hasattr(value, "get_qualified_names"):
                qnames = value.get_qualified_names()

            # If we got qnames, check if it includes the module
            if qnames:
                # Convert to list if it's a tuple
                qnames = list(qnames)

                # Check if the first element looks like a module name or class/function
                # If it starts with a capital letter or looks like a class, we need to prepend module
                module_name = self._get_module_name(value)

                # Check if qnames already includes the module
                if module_name and qnames[0] != module_name:
                    # Prepend module name to get full path
                    qnames = [module_name] + qnames

                return ".".join(qnames)

            # Fallback: Try to build contextual name (for nested functions, etc.)
            contextual_name = self._build_contextual_name(value)
            if contextual_name:
                return contextual_name

            # Fallback to attributes exposed on the value.name object
            if hasattr(value, "name"):
                if hasattr(value.name, "get_qualified_names"):
                    qnames = value.name.get_qualified_names()
                    if qnames:
                        return ".".join(qnames)
                if hasattr(value.name, "string_name"):
                    return value.name.string_name

            # Last resort: string representation
            return str(value)
        except Exception as e:
            logger.warning(f"Could not extract qualified name: {e}")
            return None

    def _get_module_name(self, value) -> Optional[str]:
        """Extract the module name from a Jedi value."""
        try:
            # Walk up to find the module context
            context = getattr(value, "parent_context", None)
            while context:
                if self._is_module_context(context):
                    return self._safe_py_name(context)
                context = getattr(context, "parent_context", None)

            # Alternative: check if value has module_name attribute
            if hasattr(value, "module_name"):
                return value.module_name

            # Try tree_name.get_root_context()
            if hasattr(value, "tree_name"):
                tree_name = value.tree_name
                if hasattr(tree_name, "get_root_context"):
                    root = tree_name.get_root_context()
                    if root:
                        return self._safe_py_name(root)
        except Exception as e:
            logger.debug(f"Could not get module name: {e}")

        return None

    def _build_contextual_name(self, value) -> Optional[str]:
        """
        Construct a qualified name by walking Jedi's parent_context chain.

        This is required for nested functions where Jedi doesn't expose
        qualified names by default (e.g., factory.build inside factory()).
        """
        try:
            parts: List[str] = []

            # Start with the value's own name
            value_name = self._safe_py_name(value)
            if not value_name:
                return None
            parts.append(value_name)

            # Walk up through parent contexts until we hit the module
            context = getattr(value, "parent_context", None)
            while context:
                if self._is_module_context(context):
                    module_name = self._safe_py_name(context)
                    if module_name:
                        parts.append(module_name)
                    break

                ctx_name = self._safe_py_name(context)
                if ctx_name:
                    parts.append(ctx_name)

                context = getattr(context, "parent_context", None)

            if parts:
                return ".".join(reversed(parts))
        except Exception as exc:
            logger.debug(f"Failed to build contextual name: {exc}")
        return None

    def _safe_py_name(self, obj) -> Optional[str]:
        """Safely call py__name__ or fall back to string_name when available."""
        name_func = getattr(obj, "py__name__", None)
        name = None
        if callable(name_func):
            name = name_func()

        if not name and hasattr(obj, "name"):
            if hasattr(obj.name, "string_name"):
                name = obj.name.string_name

        return name

    def _is_module_context(self, context: Any) -> bool:
        """Detect whether a Jedi context represents a module."""
        if context.__class__.__name__ == "ModuleContext":
            return True

        tree_node = getattr(context, "tree_node", None)
        if tree_node and getattr(tree_node, "type", None) == "file_input":
            return True

        return False
