from langchain_core.messages import AIMessage, HumanMessage

from app.agent.harness.history import build_history, latest_node_refs
from app.agent.schemas.conversation import Conversation, Message
from app.agent.schemas.parts import NodeRefPart, ReasoningPart, TextPart


def test_history_enriches_current_node_ref_collapses_past():
    past_ref = NodeRefPart(
        node_id="FunctionSchema/old",
        name="old_fn",
        node_type="function",
    )
    current_ref = NodeRefPart(
        node_id="FunctionSchema/charge",
        name="charge",
        node_type="function",
    )
    conversation = Conversation(
        id="ConversationSchema/c1",
        project_id="ProjectSchema/p1",
        messages=[
            Message(
                id="m1",
                role="user",
                parts=[past_ref, TextPart(text="first")],
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
                parts=[current_ref, TextPart(text="what does this do?")],
            ),
            Message(id="m4", role="assistant", parts=[]),
        ],
    )
    blocks = {
        "FunctionSchema/charge": (
            '<attached_node id="FunctionSchema/charge" kind="function" '
            'name="charge"><description>Charges a card.</description>'
            "</attached_node>"
        ),
    }
    messages = build_history(conversation, attached_blocks=blocks)
    assert len(messages) == 3
    assert isinstance(messages[0], HumanMessage)
    assert '<node id="FunctionSchema/old"' in messages[0].content
    assert isinstance(messages[1], AIMessage)
    assert messages[1].content == "answered"
    assert "secret" not in messages[1].content
    assert isinstance(messages[2], HumanMessage)
    assert "<attached_node" in messages[2].content
    assert "what does this do?" in messages[2].content

    refs = latest_node_refs(conversation)
    assert len(refs) == 1
    assert refs[0].name == "charge"
