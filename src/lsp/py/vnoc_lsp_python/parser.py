import re
from typing import List, Optional

import parso
from parso.python.tree import Class, Function

from vnoc_lsp_python.models import (
    BaseNode,
    CallNode,
    ClassNode,
    FunctionNode,
    NodePosition,
)

CLASS_SCHEMA = "ClassSchema"
FUNCTION_SCHEMA = "FunctionSchema"


class JediParser:
    def __init__(self, content: Optional[str] = None):
        if content is not None:
            self.content = content
            self.module = parso.parse(content)

    def _get_position(self, node) -> NodePosition:
        start_pos = node.start_pos
        end_pos = node.end_pos
        return NodePosition(
            line=start_pos[0],
            column=start_pos[1],
            end_line=end_pos[0],
            end_column=end_pos[1],
        )

    def _extract_id(self, node) -> Optional[str]:
        def get_doc_node(n):
            if hasattr(n, "get_doc_node"):
                return n.get_doc_node()
            return None

        doc_node = get_doc_node(node)
        if doc_node:
            val = doc_node.value
            if val.startswith('"""') or val.startswith("'''"):
                val = val[3:-3]
            elif val.startswith('"') or val.startswith("'"):
                val = val[1:-1]

            match = re.search(r"ID:\s*([^\s]+)", val)
            if match:
                return match.group(1).strip()
        return None

    def _is_call(self, node) -> bool:
        if node.type == "atom_expr":
            last_child = node.children[-1]
            if last_child.type == "trailer" and last_child.children[0].value == "(":
                return True
        return False

    def _visit_node(self, node) -> Optional[BaseNode]:
        if isinstance(node, Class):
            return self._visit_class(node)
        if isinstance(node, Function):
            return self._visit_function(node)
        return None

    def _scan_children(self, scope_node) -> List[BaseNode]:
        nodes = []

        def collect_nodes(current_node):
            if current_node is scope_node:
                if hasattr(current_node, "children"):
                    for child in current_node.children:
                        collect_nodes(child)
                return

            if isinstance(current_node, (Class, Function)):
                nodes.append(self._visit_node(current_node))
                return

            if self._is_call(current_node):
                nodes.extend(self._visit_call(current_node))
                if hasattr(current_node, "children"):
                    for child in current_node.children:
                        collect_nodes(child)
                return

            if hasattr(current_node, "children"):
                for child in current_node.children:
                    collect_nodes(child)

        collect_nodes(scope_node)

        seen_positions = set()
        unique_nodes = []
        for node in nodes:
            if node is None:
                continue
            pos_key = (
                node.position.line,
                node.position.column,
                node.position.end_line,
                node.position.end_column,
            )
            if pos_key not in seen_positions:
                seen_positions.add(pos_key)
                unique_nodes.append(node)

        return unique_nodes

    def _visit_class(self, node: Class) -> ClassNode:
        return ClassNode(
            id=f"{CLASS_SCHEMA}/{self._extract_id(node)}",
            name=node.name.value,
            position=self._get_position(node),
            children=self._scan_children(node),
        )

    def _visit_function(self, node: Function) -> FunctionNode:
        if node.type == "lambdef":
            return None
        target_node = node

        position = self._get_position(node)
        if node.parent and node.parent.type == "async_stmt":
            position = self._get_position(node.parent)

        return FunctionNode(
            id=f"{FUNCTION_SCHEMA}/{self._extract_id(target_node)}",
            name=node.name.value,
            position=position,
            children=self._scan_children(target_node),
        )

    def _get_clean_code(self, node) -> str:
        if hasattr(node, "children"):
            return "".join(self._get_clean_code(child) for child in node.children)
        if hasattr(node, "get_code"):
            return node.get_code(include_prefix=False)
        return ""

    def _visit_call(self, node) -> List[CallNode]:
        call_nodes: List[CallNode] = []
        prefix_children = []
        call_index = 0
        start_line, start_col = node.start_pos

        for child in node.children:
            is_call_trailer = (
                child.type == "trailer"
                and hasattr(child, "children")
                and len(child.children) > 0
                and getattr(child.children[0], "value", None) == "("
            )

            if is_call_trailer:
                name = "".join(self._get_clean_code(c) for c in prefix_children).strip()
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
                            end_column=end_col,
                        ),
                        children=[],
                        call_index=call_index,
                    )
                )
                call_index += 1

            prefix_children.append(child)

        return call_nodes

    def parse(self) -> List[BaseNode]:
        return self._scan_children(self.module)
