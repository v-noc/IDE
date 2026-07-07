from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.core.model.nodes import (
    CallNode,
    ClassNode,
    CodeElementGroupNode,
    CallGroupNode,
    FileNode,
    FolderNode,
    FunctionNode,
    ProjectNode,
    StructureGroupNode,
)

NodeKind = Literal["folder", "file", "class", "function", "call", "project", "group"]


@dataclass
class GraphNode:
    id: str
    name: str
    qname: str | None
    kind: NodeKind
    description: str
    children: list[str] = field(default_factory=list)
    line_no: int | None = None
    end_line_no: int | None = None
    target_id: str | None = None


def _is_group_id(node_id: str) -> bool:
    return "GroupSchema" in node_id


def _node_kind(node: Any) -> NodeKind:
    if isinstance(node, ProjectNode):
        return "project"
    if isinstance(node, FolderNode):
        return "folder"
    if isinstance(node, FileNode):
        return "file"
    if isinstance(node, ClassNode):
        return "class"
    if isinstance(node, FunctionNode):
        return "function"
    if isinstance(node, CallNode):
        return "call"
    if isinstance(
        node,
        (CodeElementGroupNode, CallGroupNode, StructureGroupNode),
    ):
        return "group"
    node_id = str(getattr(node, "id", "") or "")
    if "ProjectSchema" in node_id:
        return "project"
    if "FolderSchema" in node_id:
        return "folder"
    if "FileSchema" in node_id:
        return "file"
    if "ClassSchema" in node_id:
        return "class"
    if "FunctionSchema" in node_id:
        return "function"
    if "CallSchema" in node_id:
        return "call"
    if _is_group_id(node_id):
        return "group"
    return "function"


def _position(node: Any) -> tuple[int | None, int | None]:
    pos = getattr(node, "code_position", None)
    if pos is None:
        return None, None
    return pos.line_no, pos.end_line_no


def _target_id(node: Any, kind: NodeKind) -> str | None:
    if kind == "call":
        raw = getattr(node, "target_function", None)
        return str(raw) if raw else None
    if kind in ("function", "class"):
        return str(getattr(node, "id", "") or "") or None
    return None


def graph_node_from_domain(node: Any) -> GraphNode:
    kind = _node_kind(node)
    line_no, end_line_no = _position(node)
    children = sorted(str(c) for c in (getattr(node, "children", None) or set()) if c)
    return GraphNode(
        id=str(node.id),
        name=node.name,
        qname=getattr(node, "qname", None),
        kind=kind,
        description=node.description or "",
        children=children,
        line_no=line_no,
        end_line_no=end_line_no,
        target_id=_target_id(node, kind),
    )


def build_graph(
    start_id: str,
    nodes: list[Any],
) -> dict[str, GraphNode]:
    by_id: dict[str, GraphNode] = {}
    for node in nodes:
        if node is None or not getattr(node, "id", None):
            continue
        by_id[str(node.id)] = graph_node_from_domain(node)

    if start_id not in by_id and nodes:
        first = nodes[0]
        if getattr(first, "id", None):
            by_id[str(first.id)] = graph_node_from_domain(first)

    return by_id


def expand_children(
    graph: dict[str, GraphNode],
    node_id: str,
) -> list[str]:
    """Flatten group children; groups are transparent."""
    node = graph.get(node_id)
    if not node:
        return []

    ordered: list[str] = []
    for child_id in node.children:
        child = graph.get(child_id)
        if child and child.kind == "group":
            ordered.extend(expand_children(graph, child_id))
        else:
            ordered.append(child_id)
    return ordered


def sort_children_by_source(
    graph: dict[str, GraphNode],
    child_ids: list[str],
) -> list[str]:
    def sort_key(cid: str) -> tuple[int, str]:
        child = graph.get(cid)
        if child and child.line_no is not None:
            return (child.line_no, child.name)
        return (0, child.name if child else cid)

    return sorted(child_ids, key=sort_key)
