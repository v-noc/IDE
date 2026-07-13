from pydantic import TypeAdapter

from app.agent.schemas.parts import (
    DecisionPart,
    NodeRefPart,
    Part,
    ReasoningPart,
    TextPart,
    ToolPart,
    ToolPending,
)


def test_text_part_roundtrip():
    adapter = TypeAdapter(Part)
    part = adapter.validate_python({"type": "text", "text": "hello"})
    assert isinstance(part, TextPart)
    assert part.text == "hello"
    assert adapter.validate_python(part.model_dump()) == part


def test_node_ref_and_decision_roundtrip():
    adapter = TypeAdapter(Part)
    node = adapter.validate_python(
        {
            "type": "node_ref",
            "node_id": "FunctionSchema/f1",
            "name": "charge",
            "qname": "payments.charge",
            "node_type": "function",
        },
    )
    assert isinstance(node, NodeRefPart)

    decision = adapter.validate_python(
        {
            "type": "decision",
            "tool_call_id": "tc1",
            "decision": "approve",
            "overrides": {"depth": 2},
        },
    )
    assert isinstance(decision, DecisionPart)
    assert decision.overrides["depth"] == 2


def test_tool_part_nested_state():
    adapter = TypeAdapter(Part)
    part = adapter.validate_python(
        {
            "type": "tool",
            "tool_call_id": "tc1",
            "tool": "walkthrough",
            "state": {"status": "pending", "input": {"depth": 1}},
        },
    )
    assert isinstance(part, ToolPart)
    assert isinstance(part.state, ToolPending)
    assert part.state.input["depth"] == 1


def test_reasoning_part():
    adapter = TypeAdapter(Part)
    part = adapter.validate_python(
        {
            "type": "reasoning",
            "origin": "native",
            "text": "thinking…",
            "duration_ms": 1200,
        },
    )
    assert isinstance(part, ReasoningPart)
    assert part.duration_ms == 1200
