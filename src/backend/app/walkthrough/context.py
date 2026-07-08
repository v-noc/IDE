from __future__ import annotations

from dataclasses import dataclass

from app.walkthrough.schemas import VisitNode


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
    tour_position: str
    node_type: str
    mode: str
    min_blocks: int
    max_blocks: int
    start_line: int | None
    end_line: int | None
    block_focus: str | None = None
    previous_focus_lines: list[str] | None = None


def build_context(
    visit: VisitNode,
    *,
    visit_list_len: int,
    numbered_code: str | None = None,
) -> NodeContext:
    header = f"{visit.node_type} {visit.name}"
    if visit.qname:
        header = f"{header} — {visit.qname}"

    min_blocks, max_blocks = _block_bounds(visit.line_count)

    first_seen_ref = None
    if visit.first_seen_order is not None:
        first_seen_ref = f"explained at stop {visit.first_seen_order + 1}"

    return NodeContext(
        node_id=visit.node_id,
        header=header,
        description=visit.description,
        docs_excerpt="",
        parent_line="",
        child_lines=[],
        caller_line=None,
        first_seen_ref=first_seen_ref,
        numbered_code=numbered_code,
        tour_position=f"stop {visit.order + 1} of {visit_list_len}",
        node_type=visit.node_type,
        mode=visit.mode,
        min_blocks=min_blocks,
        max_blocks=max_blocks,
        start_line=visit.start_line,
        end_line=visit.end_line,
    )


def _block_bounds(line_count: int | None) -> tuple[int, int]:
    lines = line_count or 0
    max_blocks = max(2, min(6, lines // 5)) if lines else 2
    return 2, max_blocks
