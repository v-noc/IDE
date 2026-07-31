from unittest.mock import AsyncMock, patch

import pytest

from app.agent.harness.fake_runner import run_fake_enriched
from app.agent.harness.patcher import ConversationPatcher
from app.agent.schemas.conversation import Conversation, Message
from app.agent.schemas.parts import NodeRefPart, TextPart
from app.core.model.nodes import ProjectNode


@pytest.mark.asyncio
async def test_fake_enriched_mentions_attached_node():
    frames: list[dict] = []

    async def emit(frame: dict) -> None:
        frames.append(frame)

    conversation = Conversation(
        id="ConversationSchema/c1",
        project_id="ProjectSchema/p1",
        messages=[
            Message(
                id="u",
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
        ],
    )
    patcher = ConversationPatcher(conversation, emit)
    await patcher.open_conversation()
    assistant_index = await patcher.add_message(
        Message(id="a", role="assistant", parts=[]),
    )

    project = ProjectNode(
        id="ProjectSchema/p1",
        name="demo",
        description="demo project",
        local_path="/tmp",
        db_name="db",
    )
    uow = AsyncMock()
    uow.project = project
    uow.get_project_repos.return_value = AsyncMock()

    block = (
        '<attached_node id="FunctionSchema/charge" kind="function" '
        'name="charge">'
        "<description>Charges a card and returns a receipt.</description>"
        "</attached_node>"
    )

    with patch(
        "app.agent.harness.fake_runner.build_attached_blocks",
        new=AsyncMock(return_value={"FunctionSchema/charge": block}),
    ), patch(
        "app.agent.harness.fake_runner.CodeElementService",
    ):
        metadata = await run_fake_enriched(
            patcher,
            conversation=patcher.conversation,
            assistant_index=assistant_index,
            uow=uow,
            chunk_delay_s=0,
        )

    text = patcher.conversation.messages[assistant_index].parts[0].text
    assert "charge" in text
    assert "Charges a card" in text
    assert metadata.model_id == "fake:echo"
    assert metadata.stop_reason == "end_turn"
