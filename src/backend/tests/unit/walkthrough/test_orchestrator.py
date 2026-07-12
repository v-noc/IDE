from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.walkthrough.context import build_context
from app.walkthrough.orchestrator import (
    END,
    make_initial_state,
    route_after_advance,
    route_after_explain,
    route_after_intro,
)
from app.walkthrough.patcher import Patcher
from app.walkthrough.pipeline import run_pipeline
from app.walkthrough.schemas import BlockPlan, PlannedBlock, RunRequest, VisitList, VisitNode, new_session


def _visit(order: int, **kwargs) -> VisitNode:
    base = dict(
        node_id=f"fn-{order}",
        name=f"fn{order}",
        qname=f"mod.fn{order}",
        node_type="function",
        description=f"function {order}",
        level=0,
        order=order,
        parent_order=None,
        target_id=f"fn-{order}",
        mode="full",
        first_seen_order=None,
        has_code=True,
        start_line=10,
        end_line=49,
        line_count=40,
        gated=True,
    )
    base.update(kwargs)
    return VisitNode(**base)


def test_route_after_intro():
    base = make_initial_state(5)
    assert route_after_intro({**base, "stop_mode": "contextual", "stop_has_code": True, "stop_gated": True}) == "advance"
    assert route_after_intro({**base, "stop_mode": "full", "stop_has_code": False, "stop_gated": True}) == "advance"
    assert route_after_intro({**base, "stop_mode": "full", "stop_has_code": True, "stop_gated": False}) == "single_block"
    assert route_after_intro({**base, "stop_mode": "full", "stop_has_code": True, "stop_gated": True}) == "block_plan"


def test_route_after_explain():
    plan = BlockPlan(
        reasoning="two blocks",
        block_count=2,
        blocks=[
            PlannedBlock(start_line=10, end_line=20, focus="a", description="A."),
            PlannedBlock(start_line=21, end_line=30, focus="b", description="B."),
        ],
    )
    base = make_initial_state(1)
    assert route_after_explain({**base, "plan": plan, "block_cursor": 0}) == "explain_block"
    assert route_after_explain({**base, "plan": plan, "block_cursor": 1}) == "explain_block"
    assert route_after_explain({**base, "plan": plan, "block_cursor": 2}) == "advance"


def test_route_after_advance():
    base = make_initial_state(3)
    assert route_after_advance({**base, "cursor": 0}) == "intro"
    assert route_after_advance({**base, "cursor": 2}) == "intro"
    assert route_after_advance({**base, "cursor": 3}) == END


@pytest.mark.asyncio
async def test_long_tour_completes_without_recursion_error():
    """Pins recursion_limit sizing — default 25 would die on a real tour."""
    nodes = [_visit(i) for i in range(30)]
    visit_list = VisitList(start_node_id="fn-0", depth=1, nodes=nodes)

    async def get_code(node_id: str) -> dict[str, str]:
        return {"code": "\n".join(f"line {n}" for n in range(10, 50))}

    code_service = AsyncMock()
    code_service.get_code = AsyncMock(side_effect=get_code)

    session = new_session(
        RunRequest(project_id="p", node_id="fn-0", depth=1),
        visit_list,
        branch="main",
        commit_id="main@head",
        model_id="fake:fake-model",
    )
    contexts = {
        visit.order: build_context(visit, visit_list_len=len(nodes))
        for visit in nodes
    }

    frames: list[dict] = []

    async def emit(frame: dict) -> None:
        frames.append(frame)

    patcher = Patcher(session, emit)
    final = await run_pipeline(session, patcher, code_service=code_service, contexts=contexts)

    assert len(final.node_steps) == 30
    assert any(frame.get("kind") == "patch" for frame in frames)
