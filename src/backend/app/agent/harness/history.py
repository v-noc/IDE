from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.agent.schemas.conversation import Conversation, Message
from app.agent.schemas.parts import (
    NodeRefPart,
    TextPart,
    ToolPart,
)


def _node_card(part: NodeRefPart) -> str:
    q = f' qname="{part.qname}"' if part.qname else ""
    return (
        f'<node id="{part.node_id}" kind="{part.node_type}" '
        f'name="{part.name}"{q}/>'
    )


def _message_content(
    message: Message,
    *,
    enrich_node_refs: bool,
    attached_blocks: dict[str, str] | None = None,
) -> str:
    chunks: list[str] = []
    for part in message.parts:
        if isinstance(part, TextPart):
            chunks.append(part.text)
        elif isinstance(part, NodeRefPart):
            if enrich_node_refs and attached_blocks and part.node_id in attached_blocks:
                chunks.append(attached_blocks[part.node_id])
            else:
                chunks.append(_node_card(part))
        elif isinstance(part, ToolPart):
            # Phase 3: native tool pairs. Skip until then.
            continue
        # reasoning / decision dropped from history
    return "\n\n".join(c for c in chunks if c.strip())


def build_history(
    conversation: Conversation,
    *,
    attached_blocks: dict[str, str] | None = None,
    tool_hint: str | None = None,
) -> list[BaseMessage]:
    """Deterministic parts → model messages. Never rewrites user text."""
    if not conversation.messages:
        return []

    # Last user message is the current turn — enrich its node_refs fully.
    last_user_index = None
    for i in range(len(conversation.messages) - 1, -1, -1):
        if conversation.messages[i].role == "user":
            last_user_index = i
            break

    out: list[BaseMessage] = []
    for index, message in enumerate(conversation.messages):
        if message.role == "assistant" and not message.parts:
            continue  # empty skeleton mid-stream
        enrich = index == last_user_index
        # Skip the in-progress assistant message being built (empty or streaming)
        if (
            message.role == "assistant"
            and index == len(conversation.messages) - 1
            and not any(isinstance(p, TextPart) and p.text for p in message.parts)
        ):
            continue
        content = _message_content(
            message,
            enrich_node_refs=enrich,
            attached_blocks=attached_blocks if enrich else None,
        )
        if message.role == "user" and index == last_user_index and tool_hint:
            content = f"{content}\n\n<tool_hint>{tool_hint}</tool_hint>".strip()
        if not content.strip():
            continue
        if message.role == "user":
            out.append(HumanMessage(content=content))
        else:
            out.append(AIMessage(content=content))
    return out


def latest_node_refs(conversation: Conversation) -> list[NodeRefPart]:
    for message in reversed(conversation.messages):
        if message.role != "user":
            continue
        return [p for p in message.parts if isinstance(p, NodeRefPart)]
    return []
