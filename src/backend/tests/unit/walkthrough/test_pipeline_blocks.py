from __future__ import annotations

from collections import defaultdict
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.agent.llm import structured as structured_module
from app.agent.llm.fake import FakeLLM, _extract_bounds, _extract_line_range
from app.walkthrough.context import build_context
from app.walkthrough.graph import GraphNode
from app.walkthrough.patcher import Patcher
from app.walkthrough.pipeline import run_pipeline
from app.walkthrough.prompts import block_plan_user_prompt
from app.walkthrough.schemas import RunRequest, new_session
from app.walkthrough.traversal import LINE_GATE, block_bounds, build_visit_list


def _g(nodes: list[GraphNode]) -> dict[str, GraphNode]:
    return {n.id: n for n in nodes}


def _pipeline_graph() -> dict[str, GraphNode]:
    return _g(
        [
            GraphNode(
                "file",
                "service.py",
                "service.py",
                "file",
                "file",
                ["cls"],
                1,
                200,
            ),
            GraphNode(
                "cls",
                "PaymentService",
                "PaymentService",
                "class",
                "class",
                ["big_fn", "small_fn", "call_big"],
                1,
                80,
            ),
            GraphNode(
                "big_fn",
                "charge",
                "PaymentService.charge",
                "function",
                "fn",
                [],
                10,
                49,
            ),
            GraphNode(
                "small_fn",
                "tiny",
                "PaymentService.tiny",
                "function",
                "fn",
                [],
                50,
                54,
            ),
            GraphNode(
                "call_big",
                "charge",
                None,
                "call",
                "call",
                [],
                60,
                60,
                target_id="big_fn",
            ),
        ],
    )


def _code_for_node(graph: dict[str, GraphNode], node_id: str) -> dict[str, str] | None:
    node = graph[node_id]
    if node.line_no is None:
        return None
    end = node.end_line_no or node.line_no
    lines = [f"line {line_no}" for line_no in range(node.line_no, end + 1)]
    return {"code": "\n".join(lines)}


def _block_add_ops(patcher: Patcher) -> list[dict[str, Any]]:
    ops: list[dict[str, Any]] = []
    for frame in patcher.log:
        if frame.get("kind") != "patch":
            continue
        for op in frame.get("ops", []):
            path = op.get("path", "")
            if op.get("op") == "add" and path.endswith("/blocks/-"):
                ops.append(op)
    return ops


def _blocks_by_visit_order(
    patcher: Patcher,
    visit_order: int,
) -> list[dict[str, Any]]:
    node_index = patcher._index_for_order(visit_order)
    prefix = f"/node_steps/{node_index}/blocks/"
    blocks: list[dict[str, Any]] = []
    for op in _block_add_ops(patcher):
        if op["path"].startswith(prefix):
            blocks.append(op["value"])
    return blocks


def _visit_by_node_id(visit_list, node_id: str):
    return next(visit for visit in visit_list.nodes if visit.node_id == node_id)


@pytest.mark.asyncio
async def test_pipeline_emits_blocks_per_contract(monkeypatch):
    graph = _pipeline_graph()
    visit_list = build_visit_list(graph, "cls", depth=1)

    cls_visit = _visit_by_node_id(visit_list, "cls")
    big_visit = _visit_by_node_id(visit_list, "big_fn")
    small_visit = _visit_by_node_id(visit_list, "small_fn")
    call_visit = _visit_by_node_id(visit_list, "call_big")

    assert cls_visit.gated is True
    assert big_visit.gated is True
    assert small_visit.gated is False
    assert small_visit.line_count == LINE_GATE - 3
    assert call_visit.mode == "contextual"

    block_plan_calls = 0
    original_make_llm = structured_module.make_llm

    def counting_make_llm(call_type: str, **_kwargs) -> FakeLLM:
        nonlocal block_plan_calls
        if call_type == "block_plan":
            block_plan_calls += 1
        return original_make_llm(call_type)

    monkeypatch.setattr(structured_module, "make_llm", counting_make_llm)

    requested_ids: list[str] = []

    async def get_code(node_id: str) -> dict[str, str] | None:
        requested_ids.append(node_id)
        return _code_for_node(graph, node_id)

    code_service = AsyncMock()
    code_service.get_code = AsyncMock(side_effect=get_code)

    session = new_session(
        RunRequest(project_id="p", node_id="cls", depth=1),
        visit_list,
        branch="main",
        commit_id="main@head",
        model_id="fake:fake-model",
    )

    contexts = {
        visit.order: build_context(visit, visit_list_len=len(visit_list.nodes))
        for visit in visit_list.nodes
    }

    frames: list[dict[str, Any]] = []

    async def emit(frame: dict[str, Any]) -> None:
        frames.append(frame)

    patcher = Patcher(session, emit)
    final = await run_pipeline(
        session,
        patcher,
        code_service=code_service,
        contexts=contexts,
    )

    cls_blocks = _blocks_by_visit_order(patcher, cls_visit.order)
    big_blocks = _blocks_by_visit_order(patcher, big_visit.order)
    small_blocks = _blocks_by_visit_order(patcher, small_visit.order)
    call_blocks = _blocks_by_visit_order(patcher, call_visit.order)

    cls_min, cls_max = block_bounds(cls_visit.line_count)
    big_min, big_max = block_bounds(big_visit.line_count)

    assert cls_min <= len(cls_blocks) <= cls_max
    assert big_min <= len(big_blocks) <= big_max
    assert len(small_blocks) == 1
    assert len(call_blocks) == 0
    assert block_plan_calls == 2

    for visit, blocks in (
        (cls_visit, cls_blocks),
        (big_visit, big_blocks),
        (small_visit, small_blocks),
    ):
        assert visit.start_line is not None
        assert visit.end_line is not None
        for block in blocks:
            assert visit.start_line <= block["start_line"] <= visit.end_line
            assert visit.start_line <= block["end_line"] <= visit.end_line

    for node_steps in final.node_steps:
        if node_steps.mode == "contextual" or not node_steps.blocks:
            continue
        for block in node_steps.blocks:
            assert block.text

    final_blocks = defaultdict(list)
    for node_steps in final.node_steps:
        final_blocks[node_steps.node_id] = node_steps.blocks
    assert len(final_blocks["small_fn"]) == 1
    assert final_blocks["call_big"] == []

    assert "big_fn" in requested_ids


def test_fake_parses_block_plan_prompt():
    visit = _visit_by_node_id(
        build_visit_list(_pipeline_graph(), "cls", depth=1),
        "big_fn",
    )
    ctx = build_context(
        visit,
        visit_list_len=4,
        numbered_code="\n".join(
            f"{line:4d} | code" for line in range(visit.start_line, visit.end_line + 1)
        ),
    )
    prompt = block_plan_user_prompt(ctx)

    bounds = _extract_bounds(prompt)
    start, end = _extract_line_range(prompt)

    min_blocks, max_blocks = block_bounds(visit.line_count)
    assert bounds == (min_blocks, max_blocks)
    assert start == visit.start_line
    assert end == visit.end_line
