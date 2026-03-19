from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PostMessageResponse(BaseModel):
    message_id: str | None
    task_id: str
    conversation_id: str
    stream_id: str
    client_ref: str | None = None


class ConversationMetaResponse(BaseModel):
    id: str
    title: str
    description: str
    message_count: int
    has_active_task: bool
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
