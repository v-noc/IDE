import parso
from parso.python.tree import Class, Function, Name, PythonNode
from typing import List, Optional, Union
from .models import ClassNode, FunctionNode, CallNode, NodePosition, BaseNode
import re

class JediParser:
    def __init__(self, content: str):
        self.content = content
        # Use parso to parse the content. We assume Python 3.
        self.module = parso.parse(content)

    def _get_position(self, node) -> NodePosition:
        start_pos = node.start_pos
        end_pos = node.end_pos
        return NodePosition(
            line=start_pos[0],
            column=start_pos[1],
            end_line=end_pos[0],
            end_column=end_pos[1]
        )

    def _extract_id(self, node) -> Optional[str]:
        # Extract ID from docstring if available
        # Parso nodes have get_docstring() usually? 
        # Actually parso nodes are raw AST. We need to check the body.
        # But we can reuse the logic or just check the first statement.
        
        # Helper to find docstring node
        def get_doc_node(n):
            if hasattr(n, 'get_doc_node'):
                return n.get_doc_node()
            return None

        doc_node = get_doc_node(node)
        if doc_node:
            # doc_node is a String leaf usually
            val = doc_node.value
            # Remove quotes
            if val.startswith('"""') or val.startswith("'''"):
                val = val[3:-3]
            elif val.startswith('"') or val.startswith("'"):
                val = val[1:-1]
            
            match = re.search(r"ID:\s*([^\s]+)", val)
            if match:
                return match.group(1).strip()
        return None

    def _is_call(self, node) -> bool:
        if node.type == 'atom_expr':
            # Check if the last child is a trailer that looks like a call (starts with '(')
            last_child = node.children[-1]
            if last_child.type == 'trailer' and last_child.children[0].value == '(':
                return True
        return False

    def _visit_node(self, node) -> Optional[BaseNode]:
        if isinstance(node, Class):
            return self._visit_class(node)
        elif isinstance(node, Function):
            return self._visit_function(node)
        return None

    def _scan_children(self, scope_node) -> List[BaseNode]:
        children = []
        # Parso `iter_funcdefs` etc are useful but we want everything in order?
        # Or just hierarchy.
        # We can walk the children of the node.
        
        # For a Class or Function, the body is in `node.children[-1]` usually (Suite)
        # But parso has `iter_classdefs`, `iter_funcdefs`.
        # We also want Calls. Calls are expressions.
        
        # Let's define a recursive walker for the scope.
        # We only want top-level items in this scope (direct children in the hierarchy sense).
        # But Calls can be deep inside expressions.
        
        # Strategy:
        # 1. Iterate over all children of the current scope.
        # 2. If it's a Class/Function, recurse into it (it becomes a child node).
        # 3. If it's a Call, it becomes a child node (but we don't recurse *into* the call for more defs usually, though we might find calls in args).
        
        # We need a way to walk the tree *within* this scope but stop at nested scopes (inner functions/classes).
        
        # This walker is a bit aggressive. `walk_scope` will return a list of nodes found.
        # If it hits a Class/Function, it returns that Node and DOES NOT recurse into it (because `_visit_class` will handle that).
        # If it hits a Call, it returns that Call Node AND recurses into it to find nested calls? 
        # The user wants "hierarchy".
        # Class -> Function -> Call.
        # Does Class -> Call exist? Yes (class attributes).
        # Does Function -> Class exist? Yes.
        
        # Refined Strategy:
        # We are inside `_visit_class` or `_visit_function`.
        # We want to find all direct children that are Classes, Functions, or Calls.
        # But "direct" in the sense of "not inside another Class/Function".
        
        nodes = []
        
        # We can use a stack or just a recursive helper that knows the current "parent" scope.
        # But here we are just returning a list of children for `scope_node`.
        
        def collect_nodes(current_node):
            # If it's the start node, just continue to children
            if current_node is scope_node:
                if hasattr(current_node, 'children'):
                    for child in current_node.children:
                        collect_nodes(child)
                return

            if isinstance(current_node, (Class, Function)):
                # Found a nested definition.
                # Parse it fully (recursive step happens inside _visit_...)
                nodes.append(self._visit_node(current_node))
                # Do NOT recurse into its children here, because _visit_node will do that.
                return

            if self._is_call(current_node):
                nodes.append(self._visit_call(current_node))
                # We MIGHT have calls inside arguments, e.g. f(g()).
                # So we SHOULD recurse into children of the Call.
                if hasattr(current_node, 'children'):
                    for child in current_node.children:
                        collect_nodes(child)
                return

            # Continue searching
            if hasattr(current_node, 'children'):
                for child in current_node.children:
                    collect_nodes(child)

        collect_nodes(scope_node)
        return nodes

    def _visit_class(self, node: Class) -> ClassNode:
        return ClassNode(
            id=self._extract_id(node),
            name=node.name.value,
            position=self._get_position(node),
            children=self._scan_children(node)
        )

    def _visit_function(self, node: Function) -> FunctionNode:
        return FunctionNode(
            id=self._extract_id(node),
            name=node.name.value,
            position=self._get_position(node),
            children=self._scan_children(node)
        )

    def _get_clean_code(self, node) -> str:
        if hasattr(node, "children"):
            return "".join(self._get_clean_code(child) for child in node.children)
        elif hasattr(node, "get_code"):
            # Leaf nodes in parso have get_code with include_prefix
            return node.get_code(include_prefix=False)
        return ""

    def _visit_call(self, node) -> CallNode:
        # node is an atom_expr.
        # children[0] is the atom (Name) or another atom_expr.
        # We want the code up to the call trailer.
        # Simplified: just get the code of the atom part.
        
        # If it's `a.b()`, children are [atom(a), trailer(.b), trailer(())]
        # Wait, `a.b` is an atom_expr? No.
        # `a.b` is `atom_expr(atom(a), trailer(.b))`
        # `a.b()` is `atom_expr(atom(a), trailer(.b), trailer(())`
        
        # We want the name to be `a.b`.
        # We can reconstruct it from children excluding the last trailer (the call parens).
        
        parts = node.children[:-1]
        name = "".join(self._get_clean_code(c) for c in parts).strip()
        
        return CallNode(
            name=name,
            position=self._get_position(node),
            children=[]
        )

    def parse(self) -> List[BaseNode]:
        # Root level scanning
        return self._scan_children(self.module)
