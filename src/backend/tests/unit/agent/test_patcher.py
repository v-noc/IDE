import pytest

from app.agent.harness.patcher import ConversationPatcher, apply_ops
from app.agent.schemas.conversation import Conversation, Message
from app.agent.schemas.parts import TextPart


@pytest.mark.asyncio
async def test_patcher_append_and_seq():
    frames: list[dict] = []

    async def emit(frame: dict) -> None:
        frames.append(frame)

    conversation = Conversation(
        id="ConversationSchema/c1",
        project_id="ProjectSchema/p1",
        messages=[
            Message(id="msg-u", role="user", parts=[TextPart(text="hi")]),
        ],
    )
    patcher = ConversationPatcher(conversation, emit)

    await patcher.open_conversation()
    assert frames[0]["kind"] == "open"
    assert frames[0]["doc"] == "ConversationSchema/c1"

    assistant = Message(id="msg-a", role="assistant", parts=[])
    assistant_index = await patcher.add_message(assistant)
    part_index = await patcher.add_part(assistant_index, TextPart(text=""))
    await patcher.append_text(assistant_index, part_index, "Hel")
    await patcher.append_text(assistant_index, part_index, "lo")

    mirror = patcher.conversation
    assert mirror.messages[assistant_index].parts[part_index].text == "Hello"

    patch_frames = [f for f in frames if f["kind"] == "patch"]
    assert patch_frames[0]["seq"] == 0
    assert patch_frames[-1]["seq"] == len(patch_frames) - 1
    assert any(
        op.get("op") == "append"
        for f in patch_frames
        for op in f["ops"]
    )

    await patcher.set_status("idle")
    await patcher.close_doc(conversation.id, "idle")
    assert frames[-1]["kind"] == "close"
    assert frames[-1]["status"] == "idle"


def test_apply_ops_append_then_replace():
    data = {"text": "Hi", "count": 1}
    result = apply_ops(
        data,
        [
            {"op": "append", "path": "/text", "value": " there"},
            {"op": "replace", "path": "/count", "value": 2},
        ],
    )
    assert result == {"text": "Hi there", "count": 2}
