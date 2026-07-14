"""Phase 4 polish: title, usage/cost, degraded note helpers, cancel metadata."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.agent.harness.degraded import count_degraded_tools
from app.agent.harness.history import build_history
from app.agent.harness.patcher import ConversationPatcher
from app.agent.harness.stream_adapter import StreamAdapter
from app.agent.harness.title import maybe_title, title_from_user_text
from app.agent.harness.usage import estimate_cost_usd, extract_usage, merge_usage
from app.core.model.conversation import DEFAULT_CONVERSATION_NAME
from app.agent.schemas.conversation import Conversation, Message, TokenUsage
from app.agent.schemas.parts import (
    NodeRefPart,
    ReasoningPart,
    TextPart,
    ToolCompleted,
    ToolPart,
)
from app.agent.tools.base import needs_confirmation
from app.agent.tools.walkthrough_tool import WALKTHROUGH_SPEC

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_title_cases_fixture():
    data = _load("title_cases.json")
    for case in data["cases"]:
        got = title_from_user_text(case["input"])
        if "expected" in case:
            assert got == case["expected"], case
        else:
            assert got.startswith(case["expected_prefix"]), case
            assert got.endswith(case["expected_suffix"]), case


def test_maybe_title_only_when_empty():
    conversation = Conversation(
        id="ConversationSchema/c1",
        project_id="ProjectSchema/p1",
        title="",
        messages=[
            Message(
                id="m1",
                role="user",
                parts=[TextPart(text="Hello charge flow")],
            ),
        ],
    )
    assert maybe_title(conversation) == "charge flow"

    conversation.title = DEFAULT_CONVERSATION_NAME
    assert maybe_title(conversation) == "charge flow"

    conversation.title = "Already set"
    assert maybe_title(conversation) is None


def test_estimate_thresholds_fixture():
    data = _load("estimate_thresholds.json")
    from app.agent.schemas.parts import ToolEstimate
    from app.agent.tools.base import ToolSpec
    from app.agent.tools.walkthrough_tool import WalkthroughArgs

    over_threshold = ToolSpec(
        name="fixture",
        description="fixture",
        input_model=WalkthroughArgs,
        kind="task",
        confirmation="over_threshold",
        handler=None,
    )

    for case in data["cases"]:
        estimate = ToolEstimate(
            items=3,
            llm_calls=case["llm_calls"],
            label="fixture",
            over_cap=case["over_cap"],
        )
        got = needs_confirmation(
            over_threshold,
            estimate,
            case["auto_run_limit"],
        )
        assert got is case["needs_confirmation"], case["name"]


def test_history_enrichment_fixture():
    data = _load("history_enrichment.json")
    conversation = Conversation(
        id="ConversationSchema/c1",
        project_id="ProjectSchema/p1",
        messages=[
            Message(
                id="m1",
                role="user",
                parts=[
                    NodeRefPart(
                        node_id="FunctionSchema/old",
                        name="old_fn",
                        node_type="function",
                    ),
                    TextPart(text="first"),
                ],
            ),
            Message(
                id="m2",
                role="assistant",
                parts=[
                    ReasoningPart(origin="native", text="secret"),
                    TextPart(text="answered"),
                ],
            ),
            Message(
                id="m3",
                role="user",
                parts=[
                    NodeRefPart(
                        node_id="FunctionSchema/charge",
                        name="charge",
                        node_type="function",
                    ),
                    TextPart(text="what does this do?"),
                ],
            ),
            Message(id="m4", role="assistant", parts=[]),
        ],
    )
    messages = build_history(
        conversation,
        attached_blocks=data["attached_blocks"],
    )
    expect = data["expect"]
    assert len(messages) == expect["message_count"]
    assert isinstance(messages[0], HumanMessage)
    for needle in expect["past_contains"]:
        assert needle in messages[0].content
    for needle in expect["past_excludes"]:
        assert needle not in messages[0].content
    assert isinstance(messages[1], AIMessage)
    assert messages[1].content == expect["assistant_content"]
    for needle in expect["assistant_excludes"]:
        assert needle not in messages[1].content
    assert isinstance(messages[2], HumanMessage)
    for needle in expect["current_contains"]:
        assert needle in messages[2].content


def test_usage_extract_merge_and_cost():
    msg = SimpleNamespace(
        usage_metadata={
            "input_tokens": 100,
            "output_tokens": 50,
            "reasoning_tokens": 10,
        },
        response_metadata={},
    )
    usage = extract_usage(msg)
    assert usage is not None
    assert usage.input_tokens == 100
    assert usage.output_tokens == 50
    assert usage.reasoning_tokens == 10

    merged = merge_usage(usage, TokenUsage(input_tokens=20, output_tokens=5))
    assert merged is not None
    assert merged.input_tokens == 120
    assert merged.output_tokens == 55

    cost = estimate_cost_usd("openai:gpt-5-mini", merged)
    assert cost is not None
    assert cost > 0


def test_count_degraded_tools():
    conversation = Conversation(
        id="ConversationSchema/c1",
        project_id="ProjectSchema/p1",
        messages=[
            Message(id="u", role="user", parts=[TextPart(text="go")]),
            Message(
                id="a",
                role="assistant",
                parts=[
                    ToolPart(
                        tool_call_id="t1",
                        tool="walkthrough",
                        state=ToolCompleted(
                            input={},
                            result={"degraded_count": 2},
                            degraded=True,
                            duration_ms=10,
                        ),
                    ),
                ],
            ),
        ],
    )
    assert count_degraded_tools(conversation, 1) == 1
    assert count_degraded_tools(conversation, 0) == 0


@pytest.mark.asyncio
async def test_stream_adapter_metadata_usage_and_duration():
    frames: list[dict] = []

    async def emit(frame: dict) -> None:
        frames.append(frame)

    conversation = Conversation(
        id="ConversationSchema/c1",
        project_id="ProjectSchema/p1",
        messages=[Message(id="u", role="user", parts=[TextPart(text="hi")])],
    )
    patcher = ConversationPatcher(conversation, emit)
    await patcher.open_conversation()
    assistant_index = await patcher.add_message(
        Message(id="a", role="assistant", parts=[]),
    )
    adapter = StreamAdapter(
        patcher,
        assistant_index=assistant_index,
        model_id="openai:gpt-5-mini",
        prompt_version="1",
        effort="medium",
    )
    await adapter.on_message_chunk(
        SimpleNamespace(
            content="ok",
            additional_kwargs={},
            usage_metadata={"input_tokens": 10, "output_tokens": 4},
            response_metadata={},
        ),
    )
    meta = adapter.metadata()
    assert meta.prompt_version == "1"
    assert meta.usage is not None
    assert meta.usage.input_tokens == 10
    assert meta.usage.output_tokens == 4
    assert meta.cost_usd is not None
    assert meta.duration_ms is not None
    assert meta.duration_ms >= 0
    assert meta.stop_reason == "end_turn"

    adapter.mark_cancelled()
    assert adapter.metadata().stop_reason == "cancelled"


@pytest.mark.asyncio
async def test_patcher_set_title():
    frames: list[dict] = []

    async def emit(frame: dict) -> None:
        frames.append(frame)

    conversation = Conversation(
        id="ConversationSchema/c1",
        project_id="ProjectSchema/p1",
        title="",
        messages=[],
    )
    patcher = ConversationPatcher(conversation, emit)
    await patcher.open_conversation()
    await patcher.set_title("charge flow")
    assert patcher.conversation.title == "charge flow"
    assert any(
        frame.get("kind") == "patch"
        and any(op.get("path") == "/title" for op in frame.get("ops", []))
        for frame in frames
    )
