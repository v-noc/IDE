import pytest

from app.agent.schemas.parts import ToolEstimate
from app.agent.tools.base import ToolOutcome, needs_confirmation
from app.agent.harness.confirm import EstimateConfirmMiddleware


def test_estimate_confirm_middleware_limit_default():
    mw = EstimateConfirmMiddleware(auto_run_limit=15)
    assert mw.auto_run_limit == 15


def test_over_cap_skips_confirm():
    estimate = ToolEstimate(
        items=50,
        llm_calls=100,
        label="50 stops",
        over_cap=True,
    )
    # over_cap → refuse path, needs_confirmation returns False
    from app.agent.tools.walkthrough_tool import WALKTHROUGH_SPEC

    assert needs_confirmation(WALKTHROUGH_SPEC, estimate, 15) is False


@pytest.mark.asyncio
async def test_middleware_calls_on_tool_completed(monkeypatch):
    from langchain_core.messages import ToolMessage
    from pydantic import BaseModel

    from app.agent.schemas.parts import ArtifactRef, ToolEstimate
    from app.agent.tools.base import (
        ToolOutcome,
        ToolServices,
        ToolSpec,
        get_tool_registry,
        reset_tool_services,
        set_tool_services,
    )

    class _Args(BaseModel):
        x: int = 1

    class _Handler:
        async def estimate(self, _args, _services):
            return ToolEstimate(items=1, llm_calls=1, label="1", over_cap=False)

        async def run(self, _args, _services):
            return ToolOutcome(result={"status": "complete"})

    fake_spec = ToolSpec(
        name="fake_task",
        description="fake",
        input_model=_Args,
        kind="task",
        confirmation="never",
        handler=_Handler(),
    )

    completed: list[dict] = []

    async def on_completed(call_id, *, input_args, result, artifact=None, degraded=False, duration_ms=0):
        completed.append(
            {
                "call_id": call_id,
                "input_args": input_args,
                "result": result,
                "artifact": artifact,
                "degraded": degraded,
                "duration_ms": duration_ms,
            },
        )

    services = ToolServices(on_tool_completed=on_completed)
    token = set_tool_services(services)

    outcome = ToolOutcome(
        result={"status": "complete"},
        artifact=ArtifactRef(doc="walkthrough_session/x", render="walkthrough"),
    )

    async def handler(_request):
        return ToolMessage(
            content=str(outcome.result),
            tool_call_id="call-1",
            name="fake_task",
            artifact=outcome,
        )

    registry = get_tool_registry()
    monkeypatch.setitem(registry._specs, "fake_task", fake_spec)

    mw = EstimateConfirmMiddleware(auto_run_limit=15)
    request = type("Req", (), {})()
    request.tool_call = {
        "name": "fake_task",
        "id": "call-1",
        "args": {"x": 1},
    }

    try:
        await mw.awrap_tool_call(request, handler)
    finally:
        reset_tool_services(token)

    assert len(completed) == 1
    assert completed[0]["result"] == {"status": "complete"}
    assert completed[0]["artifact"].doc == "walkthrough_session/x"
