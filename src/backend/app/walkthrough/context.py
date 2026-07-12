from __future__ import annotations

from dataclasses import dataclass, field, replace

from app.core.repository import Repositories
from app.walkthrough.graph import (
    GraphNode,
    expand_children_with_groups,
    sort_children_by_source,
)
from app.walkthrough.schemas import VisitList, VisitNode
from app.walkthrough.traversal import block_bounds

_DOC_CHAR_CAP = 800
_DOCS_TOTAL_CAP = 2400
_CHILD_LINE_CAP = 20
_INTRO_FULL_MAX = 80
_INTRO_HEAD_LINES = 60


@dataclass
class NodeContext:
    node_id: str
    header: str
    description: str
    docs_excerpt: str
    parent_line: str
    child_lines: list[str]
    caller_line: str | None
    first_seen_ref: str | None
    numbered_code: str | None
    intro_code: str | None
    tour_position: str
    node_type: str
    mode: str
    min_blocks: int
    max_blocks: int
    start_line: int | None
    end_line: int | None
    child_line_entries: list[tuple[int | None, str]] = field(default_factory=list)
    block_focus: str | None = None
    block_description: str | None = None
    block_start: int | None = None
    block_end: int | None = None
    previous_block_lines: list[str] | None = None


def build_context(
    visit: VisitNode,
    *,
    visit_list_len: int,
    numbered_code: str | None = None,
    docs_excerpt: str = "",
    parent_line: str = "",
    child_lines: list[str] | None = None,
    child_line_entries: list[tuple[int | None, str]] | None = None,
    caller_line: str | None = None,
    intro_code: str | None = None,
) -> NodeContext:
    header = f"{visit.node_type} {visit.name}"
    if visit.qname:
        header = f"{header} — {visit.qname}"

    min_blocks, max_blocks = block_bounds(visit.line_count)

    first_seen_ref = None
    if visit.first_seen_order is not None:
        first_seen_ref = f"explained at stop {visit.first_seen_order + 1}"

    return NodeContext(
        node_id=visit.node_id,
        header=header,
        description=visit.description,
        docs_excerpt=docs_excerpt,
        parent_line=parent_line,
        child_lines=child_lines or [],
        child_line_entries=child_line_entries if child_line_entries is not None else [],
        caller_line=caller_line,
        first_seen_ref=first_seen_ref,
        numbered_code=numbered_code,
        intro_code=intro_code,
        tour_position=f"stop {visit.order + 1} of {visit_list_len}",
        node_type=visit.node_type,
        mode=visit.mode,
        min_blocks=min_blocks,
        max_blocks=max_blocks,
        start_line=visit.start_line,
        end_line=visit.end_line,
    )


def trim_for_intro(numbered_code: str, end_line: int) -> str:
    """Full code when <= 80 lines; else first 60 + trim marker naming end_line."""
    lines = numbered_code.splitlines()
    if len(lines) <= _INTRO_FULL_MAX:
        return numbered_code
    head = lines[:_INTRO_HEAD_LINES]
    remaining = len(lines) - _INTRO_HEAD_LINES
    marker = f"[… trimmed: {remaining} more lines, through line {end_line}]"
    return "\n".join([*head, marker])


def _one_liner(node: GraphNode, group_name: str | None = None) -> str | None:
    if not (node.description or "").strip():
        return None
    if group_name:
        kind_part = f'{node.kind}, grouped under "{group_name}"'
    else:
        kind_part = node.kind
    return f"· {node.name} ({kind_part}) — {node.description.strip()}"


def _parent_line(graph: dict[str, GraphNode], node_id: str) -> str:
    node = graph.get(node_id)
    if not node or not node.parent_id:
        return ""
    parent = graph.get(node.parent_id)
    if not parent:
        return ""
    desc = (parent.description or "").strip()
    if desc:
        return f"in {parent.kind} {parent.name} — {desc}"
    return f"in {parent.kind} {parent.name}"


def _child_line_entries(
    graph: dict[str, GraphNode],
    node_id: str,
) -> list[tuple[int | None, str]]:
    pairs = expand_children_with_groups(graph, node_id)
    child_ids = [cid for cid, _ in pairs]
    ordered_ids = sort_children_by_source(graph, child_ids)
    group_by_id = {cid: gname for cid, gname in pairs}

    entries: list[tuple[int | None, str]] = []
    for cid in ordered_ids:
        child = graph.get(cid)
        if not child:
            continue
        line = _one_liner(child, group_by_id.get(cid))
        if line:
            entries.append((child.line_no, line))

    if len(entries) > _CHILD_LINE_CAP:
        extra = len(entries) - _CHILD_LINE_CAP
        entries = [
            *entries[:_CHILD_LINE_CAP],
            (None, f"…and {extra} more"),
        ]
    return entries


def _child_lines(graph: dict[str, GraphNode], node_id: str) -> list[str]:
    return [line for _, line in _child_line_entries(graph, node_id)]


async def _docs_excerpt(repos: Repositories, document_ids: list[str]) -> str:
    parts: list[str] = []
    total = 0
    for doc_id in document_ids[:3]:
        doc = await repos.document_repo.get_by_id(doc_id)
        if doc is None:
            continue
        data = (doc.data or "").strip()
        if not data:
            continue
        if len(data) > _DOC_CHAR_CAP:
            data = data[:_DOC_CHAR_CAP].rstrip() + "[…]"
        chunk = f"### doc: {doc.name}\n{data}"
        if total + len(chunk) > _DOCS_TOTAL_CAP:
            remaining = _DOCS_TOTAL_CAP - total
            if remaining > 40:
                parts.append(chunk[:remaining].rstrip() + "[…]")
            break
        parts.append(chunk)
        total += len(chunk)
    return "\n\n".join(parts)


async def build_contexts(
    graph: dict[str, GraphNode],
    visit_list: VisitList,
    repos: Repositories,
) -> dict[int, NodeContext]:
    """One NodeContext per stop, keyed by visit order. No code fields yet."""
    contexts: dict[int, NodeContext] = {}
    n = len(visit_list.nodes)

    for visit in visit_list.nodes:
        context_node_id = visit.node_id
        if visit.node_type == "call" and visit.target_id and visit.target_id in graph:
            context_node_id = visit.target_id

        context_node = graph.get(context_node_id)
        docs_ids = list(context_node.documents) if context_node else []
        docs_excerpt = await _docs_excerpt(repos, docs_ids) if docs_ids else ""

        entries = (
            _child_line_entries(graph, context_node_id)
            if visit.mode == "full"
            else []
        )
        child_lines = [line for _, line in entries]
        parent_line = (
            _parent_line(graph, visit.node_id) if visit.mode == "full" else ""
        )

        caller_line: str | None = None
        if visit.mode == "contextual" and visit.parent_order is not None:
            caller = visit_list.nodes[visit.parent_order]
            caller_node = graph.get(caller.node_id)
            if caller_node:
                desc = (caller_node.description or "").strip()
                if desc:
                    caller_line = (
                        f"{caller_node.kind} {caller_node.name} — {desc}"
                    )
                else:
                    caller_line = f"{caller_node.kind} {caller_node.name}"
            else:
                caller_line = f"{caller.node_type} {caller.name}"

        contexts[visit.order] = build_context(
            visit,
            visit_list_len=n,
            docs_excerpt=docs_excerpt if visit.mode == "full" else "",
            parent_line=parent_line,
            child_lines=child_lines,
            child_line_entries=entries,
            caller_line=caller_line,
        )

    return contexts


def with_block_fields(
    ctx: NodeContext,
    *,
    block_focus: str,
    block_description: str,
    block_start: int,
    block_end: int,
    previous_block_lines: list[str],
) -> NodeContext:
    return replace(
        ctx,
        block_focus=block_focus,
        block_description=block_description,
        block_start=block_start,
        block_end=block_end,
        previous_block_lines=list(previous_block_lines),
    )
