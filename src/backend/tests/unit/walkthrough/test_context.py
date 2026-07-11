from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.walkthrough.context import build_contexts, trim_for_intro
from app.walkthrough.graph import GraphNode, expand_children_with_groups
from app.walkthrough.schemas import VisitList, VisitNode


def _visit(**kwargs) -> VisitNode:
    base = dict(
        node_id="fn",
        name="charge",
        qname="PaymentService.charge",
        node_type="function",
        description="charges a card",
        level=0,
        order=0,
        parent_order=None,
        target_id="fn",
        mode="full",
        first_seen_order=None,
        has_code=True,
        start_line=10,
        end_line=50,
        line_count=41,
        gated=True,
    )
    base.update(kwargs)
    return VisitNode(**base)


def test_trim_for_intro_short_unchanged():
    code = "\n".join(f"{i:4d} | line" for i in range(1, 21))
    assert trim_for_intro(code, 20) == code


def test_trim_for_intro_long_gets_marker():
    code = "\n".join(f"{i:4d} | line" for i in range(1, 101))
    trimmed = trim_for_intro(code, 144)
    assert "[… trimmed:" in trimmed
    assert "through line 144]" in trimmed
    assert trimmed.count("\n") == 60  # 60 lines + marker line


def test_expand_children_with_groups_provenance():
    graph = {
        "cls": GraphNode("cls", "C", None, "class", "c", ["grp", "direct"]),
        "grp": GraphNode("grp", "Notifications", None, "group", "", ["send"]),
        "send": GraphNode("send", "send_receipt", None, "function", "emails"),
        "direct": GraphNode("direct", "validate", None, "function", "checks"),
    }
    pairs = expand_children_with_groups(graph, "cls")
    assert ("send", "Notifications") in pairs
    assert ("direct", None) in pairs


@pytest.mark.asyncio
async def test_build_contexts_docs_and_group_child():
    graph = {
        "cls": GraphNode(
            "cls",
            "PaymentService",
            None,
            "class",
            "orchestrates payments",
            children=["grp", "fn"],
        ),
        "grp": GraphNode(
            "grp",
            "Notifications",
            None,
            "group",
            "",
            children=["send"],
            parent_id="cls",
        ),
        "fn": GraphNode(
            "fn",
            "charge",
            "PaymentService.charge",
            "function",
            "charges a card",
            documents=["DocumentSchema/doc1"],
            parent_id="cls",
            line_no=10,
            end_line_no=50,
        ),
        "send": GraphNode(
            "send",
            "send_receipt",
            None,
            "function",
            "emails the receipt",
            parent_id="grp",
            line_no=60,
            end_line_no=70,
        ),
    }

    doc = MagicMock()
    doc.name = "Charge overview"
    doc.data = "Charges a card and returns a receipt."
    repos = MagicMock()
    repos.document_repo.get_by_id = AsyncMock(return_value=doc)

    visit_list = VisitList(
        start_node_id="fn",
        depth=1,
        nodes=[
            _visit(node_id="fn", order=0),
            _visit(
                node_id="call1",
                name="charge",
                node_type="call",
                mode="contextual",
                order=1,
                parent_order=0,
                target_id="fn",
                has_code=False,
                gated=False,
                start_line=None,
                end_line=None,
                line_count=None,
            ),
        ],
    )

    contexts = await build_contexts(graph, visit_list, repos)
    ctx0 = contexts[0]
    assert "### doc: Charge overview" in ctx0.docs_excerpt
    assert ctx0.parent_line.startswith("in class PaymentService")

    from app.walkthrough.context import _child_lines

    child_lines = _child_lines(graph, "cls")
    assert any('grouped under "Notifications"' in line for line in child_lines)

    ctx1 = contexts[1]
    assert ctx1.caller_line is not None
    assert "charge" in ctx1.caller_line


@pytest.mark.asyncio
async def test_build_contexts_empty_docs():
    graph = {
        "fn": GraphNode(
            "fn",
            "charge",
            None,
            "function",
            "charges",
            documents=[],
        ),
    }
    repos = MagicMock()
    repos.document_repo.get_by_id = AsyncMock(return_value=None)
    visit_list = VisitList(
        start_node_id="fn",
        depth=0,
        nodes=[_visit()],
    )
    contexts = await build_contexts(graph, visit_list, repos)
    assert contexts[0].docs_excerpt == ""
