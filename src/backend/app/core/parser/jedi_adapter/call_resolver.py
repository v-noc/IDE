"""
CallResolver - Resolves function/method calls using Jedi's context-preserving APIs.

This module provides accurate call resolution by:
1. Preserving execution context through the call chain
2. Handling nested attributes (e.g., a.b.c())
3. Properly resolving class instantiation
4. Extracting qualified names from resolved callees
5. Extracting IDs from docstrings for direct scope lookup
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional

import jedi
from jedi.api import helpers
from jedi.inference.arguments import TreeArguments
from jedi.inference.helpers import infer_call_of_leaf
from jedi.inference.syntax_tree import infer_trailer
from jedi.inference.value import BoundMethod
from jedi.inference.value.instance import TreeInstance

from .manager import JediProjectManager

logger = logging.getLogger(__name__)


@dataclass
class CallResolutionResult:
    """Result of resolving a call site."""

    callee_id: Optional[str] = None
    """ID extracted from the callee's docstring"""

    callee_values: List[Any] = None
    """Jedi values representing the callee"""

    execution_context: Optional[Any] = None
    """Jedi execution context for the call"""

    is_class_instantiation: bool = False
    """True if this is a class instantiation (not a simple function call)"""

    qname: Optional[str] = None
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
        parent_context: Optional[Any] = None,
    ) -> List[CallResolutionResult]:
        """
        Resolve a call at the given position.

        Args:
            file_path: Path to the file
            source: Source code content
            line: Line number (1-indexed)
            column: Column number (0-indexed in Jedi)
            parent_context: Optional Jedi context from the caller (for recursion)

        Returns:
            List of CallResolutionResult objects, one for each possible callee
        """
        # Acquire lock for thread-safe Jedi operations

        try:
            script = self.jedi_manager.get_script(file_path, source)

            # Use provided parent context or fall back to module context

            position_context = script.get_context(line, column)
            if position_context.in_builtin_module() or position_context.is_stub():
                return []

            context = parent_context or script._get_module_context()

            # Find the leaf at this position
            leaf = script._module_node.get_name_of_position((line, column))

            if leaf is None:
                leaf = script._module_node.get_leaf_for_position(
                    (line, column))
                if leaf is None or leaf.type == "string":
                    return []
                if leaf.end_pos == (line, column) and leaf.type == "operator":
                    next_ = leaf.get_next_leaf()
                    if next_.start_pos == leaf.end_pos and next_.type in (
                        "number",
                        "string",
                        "keyword",
                    ):
                        leaf = next_
            try:
                # Create context at call site
                call_context = context.create_context(leaf)
            except:
                call_context = script._get_module_context().create_context(leaf)

            # Use Jedi's infer_call_of_leaf to get the callee
            # cut_own_trailer=True gives us the function/class being called
            callee_values = helpers.infer(
                script._inference_state,
                call_context,
                leaf,
            )

            if not callee_values:
                return []

            results = []
            bracket = leaf.get_next_leaf()
            trailer = bracket.parent if bracket else None

            while trailer and trailer.type != "trailer":
                trailer = trailer.parent

            for callee in callee_values:
                if callee.is_builtins_module() or callee.parent_context.is_builtins_module():
                    continue
                # Create a new result for each callee
                result = CallResolutionResult(callee_values=[callee])

                # Extract ID from docstring - PRIORITY for direct lookup
                result.callee_id = self._extract_id_from_docstring(callee)
                result.qname = self._extract_qualified_name(callee)

                if result.callee_id is None:
                    if "fastapi" in result.qname:
                        print(
                            f"No callee ID found for {result.qname} {file_path} {line}:{column}")
                    return []

                callee_for_args = callee
                if hasattr(callee, "_original_value"):
                    callee_for_args = callee._original_value

                arguments = None
                if trailer:
                    arguments = self.create_args(
                        callee_for_args,
                        trailer,
                        script._inference_state,
                        call_context,
                    )

                if callee_for_args.is_function():
                    if arguments:
                        result.execution_context = callee_for_args.as_context(
                            arguments
                        )
                    else:
                        # No trailer found, fallback to anonymous context
                        result.execution_context = callee_for_args.as_context()

                if callee_for_args.api_type == "class":
                    result.is_class_instantiation = True
                    inits = callee_for_args.py__getattribute__("__init__")
                    created_instance = TreeInstance(
                        script._inference_state,
                        callee_for_args.parent_context,
                        callee_for_args,
                        arguments,
                    )
                    if inits:
                        init_method = list(inits)[0]
                        if hasattr(init_method, "_original_value"):
                            init_method = init_method._original_value
                        bound_method = BoundMethod(
                            created_instance, callee_for_args, init_method
                        )
                        if arguments:
                            result.execution_context = bound_method.as_context(
                                arguments
                            )
                        else:
                            result.execution_context = bound_method.as_context()
                    else:
                        result.execution_context = callee_for_args.as_context()
                    logger.debug(
                        f"Resolved class instantiation: {result.callee_id}"
                    )
                else:
                    logger.debug(f"Resolved call to: {result.callee_id}")

                # Only add results with valid callee_id
                if result.callee_id:
                    results.append(result)

            return results

        except Exception as e:
            print(
                f"Error resolving call at {file_path} {line}:{column}:  {e}"
            )
            # if file_path.endswith("main.py"):
            #     with open("demo.txt", "w") as f:
            #         import traceback
            #         f.write(traceback.format_exc())
            return []

    def _extract_id_from_docstring(self, value) -> Optional[str]:
        """
        Extract ID from docstring using the same logic as parser.py.

        Args:
            value: Jedi value object

        Returns:
            Extracted ID or None
        """
        try:
            # Try to get docstring from the Jedi value
            docstring = None
            if hasattr(value, "_original_value"):
                value = value._original_value

            # Method 1: Use tree_node.get_doc_node() for parso nodes
            if hasattr(value, "tree_node") and value.tree_node:
                tree_node = value.tree_node
                if hasattr(tree_node, "get_doc_node"):
                    doc_node = tree_node.get_doc_node()
                    if doc_node:
                        val = doc_node.value
                        # Remove quotes
                        if val.startswith('"""') or val.startswith("'''"):
                            docstring = val[3:-3]
                        elif val.startswith('"') or val.startswith("'"):
                            docstring = val[1:-1]

            # Method 2: Use py__doc__() if available
            if not docstring and hasattr(value, "py__doc__"):
                try:
                    docstring = value.py__doc__()
                except:
                    pass

            # Extract ID from docstring
            if docstring:
                match = re.search(r"ID:\s*([^\s]+)", docstring)
                if match:
                    return match.group(1).strip()

            return None
        except Exception as e:
            logger.debug(f"Could not extract ID from docstring: {e}")
            return None

    def _extract_qualified_name(self, value) -> Optional[str]:
        """
        Extract fully qualified name.
        """
        try:
            value = value

            if hasattr(value, "_original_value"):
                value = value._original_value
            if hasattr(value, "name") and hasattr(value.name, "get_qualified_names"):
                qnames = value.name.get_qualified_names(True)
                if qnames:
                    return ".".join(qnames)
                return value.name.string_name
            if value.parent_context.is_module():
                return ".".join((value.parent_context.py__name__(), value.py__name__(),))
            if value.parent_context.is_class():
                return ".".join((value.parent_context.py__name__(), value.get_qualified_names(),))
            return None
        except Exception as e:
            logger.warning(f"Could not extract qualified name: {e}")
            return None

    def create_args(self, value, trailer, inference_state, context):
        arglist = trailer.children[1]
        if arglist == ")":
            arglist = None
        args = TreeArguments(inference_state, context, arglist, trailer)
        return args
