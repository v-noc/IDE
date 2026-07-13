import pytest

from app.agent.harness.echo_runner import run_echo
from app.agent.harness.patcher import ConversationPatcher
from app.agent.schemas.conversation import Conversation, Message
from app.agent.schemas.parts import TextPart
from app.core.model.conversation import ConversationNode
from app.core.model.schemas.conversation_schema import ConversationSchema


@pytest.mark.asyncio
async def test_echo_stream_persists_via_schema_roundtrip():
    """Echo streams tokens; the final mirror survives schema serialize/reload."""
    frames: list[dict] = []
    persisted: list[Conversation] = []

    async def emit(frame: dict) -> None:
        frames.append(frame)

    async def on_persist(conv: Conversation) -> None:
        persisted.append(conv.model_copy(deep=True))

    conversation = Conversation(
        id="ConversationSchema/echo-1",
        project_id="ProjectSchema/p1",
        messages=[
            Message(id="msg-u", role="user", parts=[TextPart(text="hello")]),
        ],
    )
    patcher = ConversationPatcher(conversation, emit, on_persist=on_persist)
    await patcher.open_conversation()
    await patcher.set_status("running")

    assistant = Message(id="msg-a", role="assistant", parts=[])
    assistant_index = await patcher.add_message(assistant)

    metadata = await run_echo(
        patcher,
        assistant_index=assistant_index,
        user_text="hello",
        chunk_delay_s=0,
    )
    await patcher.finalize_message(assistant_index, metadata)
    await patcher.set_status("idle")
    await patcher.close_doc(conversation.id, "idle")

    final = patcher.conversation
    assert final.status == "idle"
    assert final.messages[assistant_index].parts[0].text == "Echo: hello"
    assert final.messages[assistant_index].metadata.model_id == "fake:echo"
    assert final.messages[assistant_index].metadata.stop_reason == "end_turn"

    # Schema roundtrip == reload path (GET /conversations/{id})
    node = ConversationNode.from_conversation(final)
    schema = ConversationSchema.from_pydantic(node)
    reloaded = schema.to_pydantic().to_conversation()
    assert reloaded.messages[assistant_index].parts[0].text == "Echo: hello"

    assert any(f["kind"] == "open" for f in frames)
    assert any(f["kind"] == "close" for f in frames)
    assert any(
        op.get("op") == "append"
        for f in frames
        if f.get("kind") == "patch"
        for op in f.get("ops", [])
    )
    # set_status / finalize_message trigger on_persist
    assert len(persisted) >= 1
