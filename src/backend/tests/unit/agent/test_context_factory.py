from app.agent.context.factory import shape_attached_node
from app.agent.context.specs import get_preset
from app.agent.context.xml import render_attached_node
from app.walkthrough.graph import GraphNode


def _graph() -> dict[str, GraphNode]:
    parent = GraphNode(
        id="ClassSchema/c1",
        name="PaymentService",
        qname="payments.PaymentService",
        kind="class",
        description="Orchestrates charge and refund flows.",
        children=["FunctionSchema/charge", "FunctionSchema/refund"],
    )
    charge = GraphNode(
        id="FunctionSchema/charge",
        name="charge",
        qname="payments.PaymentService.charge",
        kind="function",
        description="Charges a card and returns a receipt.",
        children=["CallSchema/validate"],
        line_no=10,
        end_line_no=20,
        parent_id="ClassSchema/c1",
    )
    refund = GraphNode(
        id="FunctionSchema/refund",
        name="refund",
        qname="payments.PaymentService.refund",
        kind="function",
        description="Reverses a completed charge.",
        parent_id="ClassSchema/c1",
    )
    validate = GraphNode(
        id="CallSchema/validate",
        name="validate_card()",
        qname=None,
        kind="call",
        description="Checks number, expiry and cvv format.",
        parent_id="FunctionSchema/charge",
        target_id="FunctionSchema/validate_card",
    )
    # parent_id links set explicitly (build_graph would also set from children)
    parent.parent_id = None
    return {
        parent.id: parent,
        charge.id: charge,
        refund.id: refund,
        validate.id: validate,
    }


def test_shape_attached_node_includes_neighborhood():
    graph = _graph()
    spec = get_preset("attached_node")
    shaped = shape_attached_node(
        graph,
        "FunctionSchema/charge",
        spec,
        docs=[("Payment flow", "Charging happens in two phases.")],
        code="def charge(self):\n    return 1\n",
    )
    assert shaped is not None
    assert shaped.parent is not None
    assert shaped.parent.name == "PaymentService"
    assert any(s.name == "refund" for s in shaped.siblings)
    assert any(c.name == "validate_card()" for c in shaped.children)
    assert shaped.docs
    assert shaped.code is not None

    xml = render_attached_node(shaped)
    assert "<attached_node" in xml
    assert "<parent" in xml
    assert "refund" in xml
    assert "validate_card()" in xml
    assert "<description>" in xml
    assert "<code" in xml


def test_siblings_cap():
    graph = _graph()
    parent = graph["ClassSchema/c1"]
    for i in range(15):
        sid = f"FunctionSchema/extra{i}"
        graph[sid] = GraphNode(
            id=sid,
            name=f"extra{i}",
            qname=None,
            kind="function",
            description=f"extra fn {i}",
            parent_id=parent.id,
        )
        parent.children.append(sid)

    spec = get_preset("attached_node")
    shaped = shape_attached_node(graph, "FunctionSchema/charge", spec)
    assert shaped is not None
    assert len(shaped.siblings) <= spec.caps.siblings
    assert shaped.siblings_more > 0
