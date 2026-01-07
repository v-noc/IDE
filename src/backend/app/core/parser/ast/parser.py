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
                nodes.extend(self._visit_call(current_node))
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

        # Filter out duplicate nodes with the same position in the same scope
        seen_positions = set()
        unique_nodes = []
        for node in nodes:
            if node is None:
                continue
            # Create a key based on position (line, column, end_line, end_column)
            pos_key = (
                node.position.line,
                node.position.column,
                node.position.end_line,
                node.position.end_column
            )
            if pos_key not in seen_positions:
                seen_positions.add(pos_key)
                unique_nodes.append(node)

        return unique_nodes

    def _visit_class(self, node: Class) -> ClassNode:
        return ClassNode(
            id=self._extract_id(node),
            name=node.name.value,
            position=self._get_position(node),
            children=self._scan_children(node)
        )

    def _visit_function(self, node: Function) -> FunctionNode:
        if node.type == 'lambdef':
            return None
        target_node = node

        position = self._get_position(node)
        if node.parent and node.parent.type == 'async_stmt':
            position = self._get_position(node.parent)

        return FunctionNode(
            id=self._extract_id(target_node),
            name=node.name.value,
            position=position,
            children=self._scan_children(target_node)
        )

    def _get_clean_code(self, node) -> str:
        if hasattr(node, "children"):
            return "".join(self._get_clean_code(child) for child in node.children)
        elif hasattr(node, "get_code"):
            # Leaf nodes in parso have get_code with include_prefix
            return node.get_code(include_prefix=False)
        return ""

    def _visit_call(self, node) -> List[CallNode]:
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

        call_nodes: List[CallNode] = []
        prefix_children = []
        call_index = 0
        start_line, start_col = node.start_pos

        for child in node.children:
            is_call_trailer = (
                child.type == 'trailer'
                and hasattr(child, 'children')
                and len(child.children) > 0
                and getattr(child.children[0], 'value', None) == '('
            )

            if is_call_trailer:
                name = "".join(self._get_clean_code(c)
                               for c in prefix_children).strip()
                if not name and node.children:
                    name = self._get_clean_code(node.children[0]).strip()

                end_line, end_col = child.end_pos
                call_nodes.append(
                    CallNode(
                        call_col_pos=child.start_pos[1],
                        name=name,
                        position=NodePosition(
                            line=start_line,
                            column=start_col,
                            end_line=end_line,
                            end_column=end_col
                        ),
                        children=[],
                        call_index=call_index,
                    )
                )
                call_index += 1

            prefix_children.append(child)

        return call_nodes

    def parse(self) -> List[BaseNode]:
        # Root level scanning
        return self._scan_children(self.module)
