import pytest

from app.walkthrough.patcher import Patcher
from app.walkthrough.schemas import RunRequest, VisitList, VisitNode, new_session


@pytest.mark.asyncio
async def test_patcher_applies_ops_to_mirror():
    frames: list[dict] = []

    async def emit(frame: dict) -> None:
        frames.append(frame)

    request = RunRequest(project_id="ProjectSchema/p", node_id="FunctionSchema/f", depth=0)
    visit = VisitNode(
        node_id="FunctionSchema/f",
        name="charge",
        qname="charge",
        node_type="function",
        description="fn",
        level=0,
        order=0,
        parent_order=None,
        target_id="FunctionSchema/f",
        mode="full",
        first_seen_order=None,
        has_code=True,
        start_line=1,
        end_line=10,
        line_count=10,
        gated=False,
    )
    session = new_session(
        request,
        VisitList(start_node_id=visit.node_id, depth=0, nodes=[visit]),
        branch="main",
        commit_id="main@head",
        model_id="fake:fake-model",
    )
    patcher = Patcher(session, emit)

    await patcher.open_node_steps(0, visit.node_id, "full")
    await patcher.set_intro(0, "Intro text", False)
    await patcher.append_error("intro attempt 1: fake failure")

    assert len(patcher.mirror.node_steps) == 1
    assert patcher.mirror.node_steps[0].intro_text == "Intro text"
    assert patcher.mirror.error_log == ["intro attempt 1: fake failure"]
    assert frames[0]["kind"] == "patch"
    assert frames[0]["seq"] == 0
    assert any(
        op.get("path") == "/error_log/-"
        for frame in frames
        if frame.get("kind") == "patch"
        for op in frame.get("ops", [])
    )
