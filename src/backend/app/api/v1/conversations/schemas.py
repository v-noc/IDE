"""REST DTOs for conversations (aligned with agentv2 docs)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TextPartIn(BaseModel):
    type: Literal["text"] = "text"
    text: str


class PostMessageRequest(BaseModel):
    role: Literal["user"] = "user"
    parts: list[TextPartIn] = Field(..., min_length=1)


class CreateConversationRequest(BaseModel):
    title: str = Field(default="New conversation", min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)


class PostMessageResponse(BaseModel):
    message_id: str | None
    task_id: str
    conversation_id: str
    stream_id: str


class PaginatedItems(BaseModel):
    items: list[Any]
    next_cursor: str | int | None = None
    has_more: bool = False


class ConversationMetaResponse(BaseModel):
    id: str
    title: str
    description: str
    message_count: int
    has_active_task: bool
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


def task_to_wire(t: Any) -> dict[str, Any]:
    """Serialize `Task` node for JSON responses."""
    return t.model_dump(mode="json")


def subtask_to_wire(st: Any) -> dict[str, Any]:
    return st.model_dump(mode="json")
