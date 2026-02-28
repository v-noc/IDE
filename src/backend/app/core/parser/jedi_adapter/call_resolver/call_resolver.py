import logging
import re
from typing import List, Optional

from jedi.api import helpers
from jedi.api.completion import TreeInstance
from jedi.inference.finder import TreeArguments
from jedi.inference.value import BoundMethod
from parso.python.tree import Class, Function
from app.core.parser.jedi_adapter.manager import JediProjectManager
from app.core.parser.ast.parser import JediParser
from pydantic import BaseModel
from app.core.model.nodes import CodePosition
logger = logging.getLogger(__name__)


class CallFrameStack(BaseModel):
    target_qname: str
    target_id: str
    children: List['CallFrameStack'] = []

    parent: Optional['CallFrameStack'] = None

    def add_child(self, child: 'CallFrameStack') -> 'CallFrameStack':
        """Add a child node and set its parent"""
        # Check if this exact call already exists to avoid duplicates in siblings
        for existing in self.children:
            if (existing.target_qname == child.target_qname):
                existing.call_count += 1
                return existing

        self.children.append(child)
        child.parent = self
        return child

    def is_ancestor(self, qualified_name: str) -> bool:
        """Check if a node with this qualified name is already in our ancestor chain"""
        current = self
        while current:
            if current.target_qname == qualified_name:
                return True
            current = current.parent
        return False


class CallHierarchyResolver:
    def __init__(self, jedi_manager: JediProjectManager):
        self.jedi_manager = jedi_manager

    def resolve_call_hierarchy(self, file_path: str, call_positions) -> CallFrameStack:
        self.script = self.jedi_manager.get_script(file_path)
        self.file_path = file_path
        # ONE InferenceState for entire session - this is the expensive part
        self.inference_state = self.script._inference_state

        self.module_context = self.script._get_module().as_context()
        self.jedi_parser = JediParser()

        self.call_frame_stack = CallFrameStack(
            target_qname="root", target_id="root", children=[])

        self.resolve_call_hierarchy_for_node(call_positions, self.module_context,
                                             self.call_frame_stack)

        return self.call_frame_stack

    def resolve_call_hierarchy_for_node(self, call_node: any, parent_context: any, call_frame_stack):

        line = call_node.position.line
        col = call_node.call_col_pos
        pos = (line, col)
        leaf = parent_context._value.tree_node.get_name_of_position(
            (line, col))

        if leaf is None:
            leaf = parent_context._value.tree_node.get_leaf_for_position(pos)
            if leaf is None or leaf.type == 'string':
                return []
            if leaf.end_pos == (line, col) and leaf.type == 'operator':
                next_ = leaf.get_next_leaf()
                if next_.start_pos == leaf.end_pos \
                        and next_.type in ('number', 'string', 'keyword'):
                    leaf = next_

        call_context = parent_context.create_context(leaf)
        callee_values = helpers.infer(
            self.inference_state,
            call_context,
            leaf,
        )

        if not callee_values:
            print(f"no callee values", leaf)
            return []

        bracket = leaf.get_next_leaf()
        trailer = bracket.parent if bracket else None

        while trailer and trailer.type != "trailer":
            trailer = trailer.parent

        visited_qnames = set()

        for callee in callee_values:
            callee_for_args = callee
            if hasattr(callee, "_original_value"):
                callee_for_args = callee._original_value

            if not self._is_project_code(callee_for_args, self.inference_state):
                continue

            qname = self._get_qname(callee_for_args)

            if qname is None:
                continue

            if qname in visited_qnames:
                continue

            visited_qnames.add(qname)

            target_id = self._extract_id_from_docstring(callee_for_args)

            if call_frame_stack.is_ancestor(qname):
                continue
            new_call_frame = CallFrameStack(
                target_qname=qname, target_id=target_id, children=[])
            current_call_frame = call_frame_stack.add_child(
                new_call_frame)

            arguments = None
            if trailer:
                arguments = self.create_args(
                    callee_for_args,
                    trailer,
                    self.inference_state,
                    call_context,
                )

            if callee_for_args.is_function():
                if arguments:
                    function_context = callee_for_args.as_context(
                        arguments)
                else:
                    # No trailer found, fallback to anonymous context.
                    function_context = callee_for_args.as_context()

                function_node = getattr(callee_for_args, "tree_node", None)
                if function_node is None:
                    continue

                self._analyze_function(
                    function_node,
                    function_context,
                    current_call_frame
                )
            elif callee_for_args.api_type == "class":
                inits = callee_for_args.py__getattribute__("__init__")
                created_instance = TreeInstance(
                    self.inference_state,
                    callee_for_args.parent_context,
                    callee_for_args,
                    arguments,
                )
                if inits:
                    init_method = list(inits)[0]
                    bound_method = BoundMethod(
                        created_instance, callee_for_args, init_method
                    )
                    init_tree_node = getattr(
                        init_method, "tree_node", None)
                    if arguments:
                        execution_context = bound_method.as_context(
                            arguments
                        )
                    else:
                        execution_context = bound_method.as_context()

                    self._analyze_function(
                        init_tree_node, execution_context, current_call_frame)

    def _analyze_function(self, function_node, function_context, call_frame_stack):
        call_nodes = []

        def collect_call_node(child):
            if isinstance(child, (Class, Function)):
                return
            if self.jedi_parser._is_call(child):
                call_nodes.extend(self.jedi_parser._visit_call(child))
            # We MIGHT have calls inside arguments, e.g. f(g()).
            # So we SHOULD recurse into children of the Call.
            if hasattr(child, 'children'):
                for child in child.children:
                    collect_call_node(child)

        for child in function_node.children:
            collect_call_node(child)

        for call_node in call_nodes:
            self.resolve_call_hierarchy_for_node(
                call_node, function_context, call_frame_stack)

    def _get_qname(self, node_value):

        if hasattr(node_value, "name") and hasattr(node_value.name, "get_qualified_names"):
            qnames = node_value.name.get_qualified_names(True)
            if qnames:
                qualified_name = ".".join(qnames)
                return qualified_name

        if hasattr(node_value, "tree_node"):
            return self._get_qname(node_value.parent_context) + "." + node_value.tree_node.name.value
        return None

    def _is_project_code(self, callee, inference_state):
        """Check if callee is defined in project code (not builtin/stdlib/external)."""
        # 1. Skip C builtins (sys, os, etc.)
        if callee.is_builtins_module():
            print(f"is_builtins_module: {callee}")
            return False

        # 2. Get the module context and file path
        module_context = callee.get_root_context()
        module_path = module_context.py__file__()

        if module_path is None:
            print(f"module_path is None", callee)
            return False  # Shouldn't happen if not builtin, but safety check

        # 3. Compare to project path
        project = inference_state.project
        project_path = getattr(project, 'path', None) or getattr(
            project, '_path', None)

        if project_path:
            import os
            # Normalize for cross-platform comparison
            norm_module = os.path.normcase(os.path.abspath(module_path))
            norm_project = os.path.normcase(os.path.abspath(project_path))

            if norm_module.startswith(norm_project):
                return True

        # 4. Optional: Explicitly exclude stdlib and site-packages
        # (Useful if project path check fails or you want to be extra sure)
        norm_path = os.path.normcase(module_path)
        if 'site-packages' in norm_path:
            return False
        if 'lib/python' in norm_path and 'site-packages' not in norm_path:
            # Heuristic for stdlib location
            return False
        if hasattr(module_context, 'is_stdlib') and module_context.is_stdlib():
            return False
        print(f"module_context is not stdlib", module_context)

        return False  # Default to False (external) if uncertain

    def create_args(self, value, trailer, inference_state, context):
        arglist = trailer.children[1]
        if arglist == ")":
            arglist = None
        args = TreeArguments(inference_state, context, arglist, trailer)
        return args

    def _extract_id_from_docstring(self, node_value):
        docstring = None
        if hasattr(node_value, "tree_node") and node_value.tree_node:
            tree_node = node_value.tree_node
            if hasattr(tree_node, "get_doc_node"):
                doc_node = tree_node.get_doc_node()
                if doc_node:
                    val = doc_node.value
                    # Remove quotes
                    if val.startswith('"""') or val.startswith("'''"):
                        docstring = val[3:-3]
                    elif val.startswith('"') or val.startswith("'"):
                        docstring = val[1:-1]

        if docstring:
            match = re.search(r"ID:\s*([^\s]+)", docstring)
            if match:
                return match.group(1).strip()
