import pytest

from app.agent.harness.patcher import ConversationPatcher
from app.agent.harness.tool_tracker import ToolPartTracker
from app.agent.schemas.conversation import Conversation, Message
from app.agent.schemas.parts import (
    ArtifactRef,
    TextPart,
    ToolCompleted,
    ToolPart,
    ToolPending,
)


@pytest.mark.asyncio
async def test_tracker_pending_running_completed_preserves_input():
    frames: list[dict] = []

    async def emit(frame: dict) -> None:
        frames.append(frame)

    conversation = Conversation(
        id="ConversationSchema/c1",
        project_id="ProjectSchema/p1",
        messages=[Message(id="u", role="user", parts=[TextPart(text="go")])],
    )
    patcher = ConversationPatcher(conversation, emit)
    await patcher.open_conversation()
    assistant_index = await patcher.add_message(
        Message(id="a", role="assistant", parts=[]),
    )
    tracker = ToolPartTracker(patcher, assistant_index)

    input_args = {"node_id": "FunctionSchema/f1", "depth": 2}
    await tracker.pending("call-1", "walkthrough", input_args)
    await tracker.running("call-1", input_args)
    await tracker.completed(
        "call-1",
        input_args=input_args,
        result={"status": "complete", "stops": 3},
        artifact=ArtifactRef(doc="walkthrough_session/abc", render="walkthrough"),
        duration_ms=1200,
    )

    part = patcher.conversation.messages[assistant_index].parts[0]
    assert isinstance(part, ToolPart)
    assert isinstance(part.state, ToolCompleted)
    assert part.state.input == input_args
    assert part.state.artifact is not None
    assert part.state.artifact.doc == "walkthrough_session/abc"


@pytest.mark.asyncio
async def test_tracker_pending_twice_does_not_duplicate():
    frames: list[dict] = []

    async def emit(frame: dict) -> None:
        frames.append(frame)

    conversation = Conversation(
        id="ConversationSchema/c1",
        project_id="ProjectSchema/p1",
        messages=[Message(id="u", role="user", parts=[TextPart(text="go")])],
    )
    patcher = ConversationPatcher(conversation, emit)
    await patcher.open_conversation()
    assistant_index = await patcher.add_message(
        Message(id="a", role="assistant", parts=[]),
    )
    tracker = ToolPartTracker(patcher, assistant_index)

    input_args = {"node_id": "FunctionSchema/f1", "depth": 2}
    await tracker.pending("call-1", "walkthrough", input_args)

    # Simulate resume: fresh tracker, part already in conversation
    resumed = ToolPartTracker(patcher, assistant_index)
    await resumed.pending("call-1", "walkthrough", input_args)

    parts = patcher.conversation.messages[assistant_index].parts
    tool_parts = [p for p in parts if isinstance(p, ToolPart)]
    assert len(tool_parts) == 1
    assert isinstance(tool_parts[0].state, ToolPending)


@pytest.mark.asyncio
async def test_close_doc_persists_artifact_snapshot():
    frames: list[dict] = []
    persisted: list[Conversation] = []

    async def emit(frame: dict) -> None:
        frames.append(frame)

    async def on_persist(conv: Conversation) -> None:
        persisted.append(conv.model_copy(deep=True))

    conversation = Conversation(
        id="ConversationSchema/c1",
        project_id="ProjectSchema/p1",
        messages=[],
    )
    patcher = ConversationPatcher(conversation, emit, on_persist=on_persist)
    await patcher.open_conversation()

    artifact_id = "walkthrough_session/abc123"
    snapshot = {"id": "abc123", "node_steps": [{"node_id": "n1"}]}
    await patcher.open_doc(artifact_id, snapshot)
    await patcher.close_doc(artifact_id, "complete")

    assert artifact_id in patcher.conversation.artifacts
    assert patcher.conversation.artifacts[artifact_id] == snapshot
    assert len(persisted) >= 1
    assert artifact_id in persisted[-1].artifacts
