from types import SimpleNamespace

import pytest

from langchain_core.messages import ToolMessage

from app.agent.harness.patcher import ConversationPatcher
from app.agent.harness.stream_adapter import StreamAdapter
from app.agent.schemas.conversation import Conversation, Message
from app.agent.schemas.parts import ReasoningPart, TextPart


@pytest.mark.asyncio
async def test_stream_adapter_text_and_reasoning():
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
        model_id="fake:test",
        prompt_version="1",
        effort="medium",
    )

    await adapter.on_message_chunk(
        SimpleNamespace(
            content="",
            additional_kwargs={"reasoning_content": "thinking…"},
        ),
    )
    await adapter.on_message_chunk(
        SimpleNamespace(content="Hello ", additional_kwargs={}),
    )
    await adapter.on_message_chunk(
        SimpleNamespace(content="world", additional_kwargs={}),
    )

    final = patcher.conversation.messages[assistant_index]
    assert any(isinstance(p, ReasoningPart) for p in final.parts)
    text_parts = [p for p in final.parts if isinstance(p, TextPart)]
    assert len(text_parts) == 1
    assert text_parts[0].text == "Hello world"
    meta = adapter.metadata()
    assert meta.model_id == "fake:test"
    assert meta.stop_reason == "end_turn"


@pytest.mark.asyncio
async def test_stream_adapter_ignores_tool_messages():
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
        model_id="fake:test",
        prompt_version="1",
        effort="medium",
    )

    await adapter.on_message_chunk(
        SimpleNamespace(content="Before ", additional_kwargs={}),
    )
    await adapter.on_message_chunk(
        ToolMessage(content="{'x': 1}", tool_call_id="c1"),
    )
    await adapter.on_message_chunk(
        SimpleNamespace(content="after", additional_kwargs={}),
    )

    text_parts = [
        p
        for p in patcher.conversation.messages[assistant_index].parts
        if isinstance(p, TextPart)
    ]
    assert len(text_parts) == 1
    assert text_parts[0].text == "Before after"
