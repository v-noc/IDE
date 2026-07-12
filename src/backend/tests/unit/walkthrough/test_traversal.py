import pytest

from app.walkthrough.graph import GraphNode
from app.walkthrough.traversal import (
    LINE_GATE,
    VISIT_CAP,
    block_bounds,
    build_visit_list,
    compute_estimate,
)


def _g(nodes: list[GraphNode]) -> dict[str, GraphNode]:
    return {n.id: n for n in nodes}


def test_calls_before_siblings_source_order():
    nodes = [
        GraphNode("file", "service.py", "service.py", "file", "file", ["cls"]),
        GraphNode("cls", "PaymentService", "PaymentService", "class", "class", ["charge", "refund"], 1, 80),
        GraphNode("charge", "charge", "PaymentService.charge", "function", "fn", ["call_validate", "call_send"], 10, 62),
        GraphNode("call_validate", "validate_card", None, "call", "call", [], 12, 12, target_id="validate_fn"),
        GraphNode("call_send", "send_receipt", None, "call", "call", [], 30, 30, target_id="send_fn"),
        GraphNode("validate_fn", "validate_card", "validate_card", "function", "helper", [], 5, 28),
        GraphNode("send_fn", "send_receipt", "send_receipt", "function", "helper", [], 1, 20),
        GraphNode("refund", "refund", "PaymentService.refund", "function", "fn", ["call_charge_ctx"], 70, 90),
        GraphNode("call_charge_ctx", "charge", None, "call", "call", [], 72, 72, target_id="charge"),
    ]
    graph = _g(nodes)
    visit = build_visit_list(graph, "charge", depth=1)

    names = [n.name for n in visit.nodes]
    assert names[0] == "charge"
    assert names[1] == "validate_card"
    assert names[2] == "send_receipt"
    assert visit.nodes[1].mode == "full"
    assert visit.nodes[1].target_id == "validate_fn"


def test_contextual_duplicate_call():
    nodes = [
        GraphNode("fn", "charge", "charge", "function", "fn", ["c1", "c2"], 1, 40),
        GraphNode("c1", "validate", None, "call", "call", [], 5, 5, target_id="helper"),
        GraphNode("c2", "validate", None, "call", "call", [], 20, 20, target_id="helper"),
        GraphNode("helper", "validate", "validate", "function", "helper", [], 1, 10),
    ]
    graph = _g(nodes)
    visit = build_visit_list(graph, "fn", depth=1)

    modes = [n.mode for n in visit.nodes if n.node_type == "call"]
    assert modes == ["full", "contextual"]
    assert visit.nodes[2].first_seen_order == 1


def test_recursion_is_contextual():
    nodes = [
        GraphNode("f", "f", "f", "function", "recurses", ["c"], 1, 20),
        GraphNode("c", "f", None, "call", "call", [], 5, 5, target_id="f"),
    ]
    graph = _g(nodes)
    visit = build_visit_list(graph, "f", depth=2)

    assert len(visit.nodes) == 2
    assert visit.nodes[1].mode == "contextual"


def test_depth_limits_descent():
    nodes = [
        GraphNode("a", "a", "a", "function", "a", ["b"], 1, 10),
        GraphNode("b", "b", "b", "function", "b", ["c"], 1, 10),
        GraphNode("c", "c", "c", "function", "c", [], 1, 10),
    ]
    graph = _g(nodes)
    visit = build_visit_list(graph, "a", depth=1)
    assert [n.name for n in visit.nodes] == ["a", "b"]


def test_groups_are_transparent():
    nodes = [
        GraphNode("fn", "fn", "fn", "function", "fn", ["grp"], 1, 10),
        GraphNode("grp", "group", None, "group", "group", ["child"], None, None),
        GraphNode("child", "child", "child", "function", "child", [], 2, 8),
    ]
    graph = _g(nodes)
    visit = build_visit_list(graph, "fn", depth=1)
    assert [n.name for n in visit.nodes] == ["fn", "child"]
    assert all(n.node_type != "group" for n in visit.nodes)


def test_line_gate_single_block():
    nodes = [
        GraphNode("fn", "tiny", "tiny", "function", "small", [], 1, LINE_GATE - 1),
    ]
    graph = _g(nodes)
    visit = build_visit_list(graph, "fn", depth=0)
    assert visit.nodes[0].gated is False
    assert visit.nodes[0].line_count == LINE_GATE - 1


def test_estimate_arithmetic():
    nodes = [
        GraphNode("fn", "charge", "charge", "function", "fn", [], 1, 40),
    ]
    graph = _g(nodes)
    visit = build_visit_list(graph, "fn", depth=0)
    est = compute_estimate(visit)
    assert est.node_count == 1
    assert est.step_estimate >= 2
    assert est.over_cap is False


def test_block_bounds_values():
    assert block_bounds(7) == (2, 2)
    assert block_bounds(10) == (2, 2)
    assert block_bounds(30) == (2, 6)


def test_over_cap_flag():
    child_ids = [f"fn{i}" for i in range(50)]
    nodes = [
        GraphNode(
            "file",
            "wide.py",
            "wide.py",
            "file",
            "file",
            child_ids,
            1,
            200,
        ),
    ]
    for index, child_id in enumerate(child_ids):
        nodes.append(
            GraphNode(
                child_id,
                f"fn{index}",
                f"fn{index}",
                "function",
                "x",
                [],
                index + 2,
                index + 10,
            ),
        )
    graph = _g(nodes)
    visit = build_visit_list(graph, "file", depth=1)
    est = compute_estimate(visit)
    assert est.over_cap is True
    assert len(visit.nodes) == VISIT_CAP
