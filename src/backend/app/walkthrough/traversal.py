from __future__ import annotations

import math
from typing import Literal

from app.walkthrough.graph import GraphNode, expand_children, sort_children_by_source
from app.walkthrough.schemas import Estimate, VisitList, VisitNode

LINE_GATE = 8
VISIT_CAP = 40
MAX_DEPTH = 3

StopKind = Literal["folder", "file", "class", "function", "call", "project"]


def _stop_kind(kind: str) -> StopKind | None:
    if kind in ("folder", "file", "class", "function", "call", "project"):
        return kind  # type: ignore[return-value]
    return None


def _line_count(node: GraphNode) -> int | None:
    if node.line_no is None or node.end_line_no is None:
        return None
    return max(0, node.end_line_no - node.line_no + 1)


def _has_code(node: GraphNode, graph: dict[str, GraphNode]) -> bool:
    if node.kind in ("function", "class"):
        return node.line_no is not None
    if node.kind == "call":
        if not node.target_id:
            return False
        target = graph.get(node.target_id)
        return target is not None and target.line_no is not None
    return False


def _code_bounds(
    node: GraphNode,
    graph: dict[str, GraphNode],
) -> tuple[int | None, int | None, int | None]:
    if node.kind in ("function", "class"):
        return node.line_no, node.end_line_no, _line_count(node)
    if node.kind == "call" and node.target_id:
        target = graph.get(node.target_id)
        if target:
            return target.line_no, target.end_line_no, _line_count(target)
    return None, None, None


def _block_bounds(line_count: int | None) -> tuple[int, int]:
    lines = line_count or 0
    max_blocks = max(2, min(6, lines // 5))
    return 2, max_blocks


def _est_blocks(visit: VisitNode) -> int:
    if visit.mode == "contextual" or not visit.has_code:
        return 0
    if not visit.gated:
        return 1
    lines = visit.line_count or 0
    return max(2, min(6, math.ceil(lines / 15)))


def compute_estimate(visit_list: VisitList) -> Estimate:
    nodes = visit_list.nodes
    node_count = len(nodes)
    over_cap = node_count > VISIT_CAP

    step_estimate = sum(1 + _est_blocks(node) for node in nodes)
    llm_call_estimate = (
        node_count
        + sum(1 for node in nodes if node.mode == "full" and node.gated)
        + sum(_est_blocks(node) for node in nodes)
    )

    return Estimate(
        node_count=node_count,
        step_estimate=step_estimate,
        llm_call_estimate=llm_call_estimate,
        over_cap=over_cap,
    )


def build_visit_list(
    graph: dict[str, GraphNode],
    start_node_id: str,
    depth: int,
) -> VisitList:
    depth = max(0, min(depth, MAX_DEPTH))
    if start_node_id not in graph:
        return VisitList(start_node_id=start_node_id, depth=depth, nodes=[])

    explained: dict[str, int] = {}
    visits: list[VisitNode] = []
    order = 0

    def visit(
        node_id: str,
        level: int,
        parent_order: int | None,
    ) -> None:
        nonlocal order

        if len(visits) >= VISIT_CAP:
            return

        node = graph.get(node_id)
        if not node:
            return

        stop = _stop_kind(node.kind)
        if stop is None:
            for child_id in sort_children_by_source(
                graph,
                expand_children(graph, node_id),
            ):
                visit(child_id, level, parent_order)
            return

        tid = node.target_id
        first_seen = explained.get(tid) if tid else None
        mode: Literal["full", "contextual"] = (
            "contextual" if tid and tid in explained else "full"
        )

        start_line, end_line, line_count = _code_bounds(node, graph)
        has_code = _has_code(node, graph)
        gated = (
            mode == "full"
            and has_code
            and line_count is not None
            and line_count >= LINE_GATE
        )

        current_order = order
        visits.append(
            VisitNode(
                node_id=node.id,
                name=node.name,
                qname=node.qname,
                node_type=stop,
                description=node.description,
                level=level,
                order=current_order,
                parent_order=parent_order,
                target_id=tid,
                mode=mode,
                first_seen_order=first_seen if mode == "contextual" else None,
                has_code=has_code,
                start_line=start_line,
                end_line=end_line,
                line_count=line_count,
                gated=gated,
            ),
        )
        order += 1

        if mode == "full" and tid:
            explained[tid] = current_order

        if mode != "full":
            return

        child_ids = sort_children_by_source(
            graph,
            expand_children(graph, node_id),
        )
        for child_id in child_ids:
            child = graph.get(child_id)
            if not child:
                continue
            child_level = level + 1
            if child_level > depth:
                continue
            visit(child_id, child_level, current_order)

    visit(start_node_id, 0, None)

    return VisitList(
        start_node_id=start_node_id,
        depth=depth,
        nodes=visits,
    )
