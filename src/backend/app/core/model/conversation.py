from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from app.agent.schemas.constants import HARNESS_SCHEMA_VERSION
from app.agent.schemas.conversation import Conversation, ConversationStatus, Message


class ConversationNode(BaseModel):
    """Persistence DTO for TerminusDB — maps 1:1 with ConversationSchema."""

    id: str
    project_id: str
    title: str = ""
    status: ConversationStatus = "idle"
    schema_version: str = HARNESS_SCHEMA_VERSION
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_conversation(self) -> Conversation:
        return Conversation(
            id=self.id,
            project_id=self.project_id,
            title=self.title,
            created_at=self.created_at,
            updated_at=self.updated_at,
            status=self.status,
            messages=list(self.messages),
            schema_version=self.schema_version,
        )

    @staticmethod
    def from_conversation(conversation: Conversation) -> ConversationNode:
        return ConversationNode(
            id=conversation.id,
            project_id=conversation.project_id,
            title=conversation.title,
            status=conversation.status,
            schema_version=conversation.schema_version,
            messages=list(conversation.messages),
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    @staticmethod
    def from_raw_dict(raw_dict: dict[str, Any]) -> ConversationNode:
        messages_raw = raw_dict.get("messages_json") or raw_dict.get("messages") or "[]"
        if isinstance(messages_raw, str):
            import orjson

            messages_data = orjson.loads(messages_raw) if messages_raw else []
        else:
            messages_data = messages_raw

        return ConversationNode(
            id=raw_dict.get("@id") or raw_dict["id"],
            project_id=raw_dict["project_id"],
            title=raw_dict.get("title") or "",
            status=raw_dict.get("status") or "idle",
            schema_version=raw_dict.get("schema_version") or HARNESS_SCHEMA_VERSION,
            messages=[Message.model_validate(m) for m in messages_data],
            created_at=raw_dict["created_at"],
            updated_at=raw_dict["updated_at"],
        )
