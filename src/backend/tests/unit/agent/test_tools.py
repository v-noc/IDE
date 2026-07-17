from app.agent.schemas.parts import ToolEstimate
from app.agent.tools.base import (
    ToolSpec,
    get_tool_registry,
    needs_confirmation,
)
from app.agent.tools.walkthrough_tool import WalkthroughArgs, WALKTHROUGH_SPEC
from app.walkthrough.schemas import RunRequest


def test_walkthrough_registered():
    registry = get_tool_registry()
    spec = registry.get("walkthrough")
    assert spec.name == "walkthrough"
    assert spec.kind == "task"
    assert spec.confirmation == "always"
    assert "walkthrough" in registry.tools_blurb()


def test_walkthrough_args_schema():
    args = WalkthroughArgs(
        node_id="FunctionSchema/f1",
        depth=2,
        user_query="how retries work",
        verbosity="quick",
    )
    assert args.depth == 2
    dumped = args.model_dump()
    assert dumped["verbosity"] == "quick"


def test_needs_confirmation_threshold():
    estimate = ToolEstimate(
        items=3,
        llm_calls=10,
        label="3 stops · ~10 LLM calls",
        over_cap=False,
    )
    assert needs_confirmation(WALKTHROUGH_SPEC, estimate, limit=15) is True
    assert needs_confirmation(WALKTHROUGH_SPEC, estimate, limit=5) is True

    always = ToolSpec(
        name="x",
        description="x",
        input_model=WalkthroughArgs,
        kind="task",
        confirmation="always",
        handler=None,
    )
    assert needs_confirmation(always, estimate, limit=100) is True


def test_walkthrough_always_confirms():
    estimate = ToolEstimate(items=1, llm_calls=1, label="1 stop", over_cap=False)
    assert needs_confirmation(WALKTHROUGH_SPEC, estimate, 15) is True


def test_walkthrough_run_request_threads_knobs():
    args = WalkthroughArgs(
        node_id="FunctionSchema/f1",
        depth=2,
        user_query="how retries work",
        verbosity="detailed",
    )
    request = RunRequest(
        project_id="ProjectSchema/p",
        node_id=args.node_id,
        depth=args.depth,
        user_query=args.user_query,
        verbosity=args.verbosity,
    )
    assert request.verbosity == "detailed"
    assert request.user_query == "how retries work"
