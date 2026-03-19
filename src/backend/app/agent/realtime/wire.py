"""Map domain models to the JSON shape the client keeps for patches / API responses."""

from __future__ import annotations

from typing import Any

from app.core.model.conversation_domain import (
    ConversationMessage,
    ConversationSummary,
    MessagePart,
    TaskPart,
    TextPart,
    ToolCallPart,
)


def _part_to_wire(part: MessagePart) -> dict[str, Any]:
    if isinstance(part, TextPart):
        return {"type": "text", "text": part.text}
    if isinstance(part, TaskPart):
        return {
            "type": "task",
            "task_id": part.task_id,
            "title": part.title,
            "description": part.description,
            "state": part.state.value,
            "progress": part.progress,
            "sub_tasks": [st.model_dump(mode="json") for st in part.sub_tasks],
            "workflow_name": part.workflow_name,
        }
    if isinstance(part, ToolCallPart):
        d: dict[str, Any] = {
            "type": "tool_call",
            "tool_name": part.tool_name,
            "tool_input": part.tool_input,
        }
        if part.tool_output is not None:
            d["tool_output"] = part.tool_output
        return d
    return part.model_dump(mode="json")  # event / future parts


def conversation_message_to_wire(msg: ConversationMessage) -> dict[str, Any]:
    return {
        "id": msg.id,
        "role": msg.role.value if hasattr(msg.role, "value") else str(msg.role),
        "sequence": msg.sequence,
        "parts": [_part_to_wire(p) for p in msg.parts],
        "created_at": msg.created_at.isoformat(),
        "token_count": msg.token_count,
        "model": msg.model,
    }


def conversation_summary_to_wire(s: ConversationSummary) -> dict[str, Any]:
    return {
        "id": s.id,
        "title": s.title,
        "description": s.description,
        "message_count": s.message_count,
        "has_active_task": s.has_active_task,
        "created_at": s.created_at.isoformat(),
        "updated_at": s.updated_at.isoformat(),
    }
