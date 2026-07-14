from app.core.model.conversation import (
    DEFAULT_CONVERSATION_NAME,
    ConversationNode,
    conversation_display_name,
)
from app.agent.schemas.conversation import Conversation


def test_conversation_display_name_defaults():
    assert conversation_display_name("") == DEFAULT_CONVERSATION_NAME
    assert conversation_display_name("  ") == DEFAULT_CONVERSATION_NAME
    assert conversation_display_name("charge flow") == "charge flow"


def test_conversation_node_name_follows_title():
    conv = Conversation(
        id="ConversationSchema/c1",
        project_id="ProjectSchema/p1",
        title="",
    )
    node = ConversationNode.from_conversation(conv)
    assert node.name == DEFAULT_CONVERSATION_NAME
    assert node.title == ""

    conv.title = "how retries work"
    node = ConversationNode.from_conversation(conv)
    assert node.name == "how retries work"
    assert node.title == "how retries work"
