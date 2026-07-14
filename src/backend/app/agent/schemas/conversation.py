from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.agent.schemas.constants import HARNESS_SCHEMA_VERSION
from app.agent.schemas.parts import Part


ConversationStatus = Literal["idle", "running", "awaiting_confirmation", "error"]
EffortLevel = Literal["off", "low", "medium", "high"]
StopReason = Literal["end_turn", "max_steps", "cancelled", "error"]


class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cache_read_tokens: int = 0


class MessageMetadata(BaseModel):
    model_id: str | None = None
    prompt_version: str | None = None
    effort: EffortLevel | None = None
    usage: TokenUsage | None = None
    cost_usd: float | None = None
    duration_ms: int | None = None
    stop_reason: StopReason | None = None
    error: str | None = None


class Message(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    parts: list[Part] = Field(default_factory=list)
    metadata: MessageMetadata = Field(default_factory=MessageMetadata)


class Conversation(BaseModel):
    id: str
    project_id: str
    title: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: ConversationStatus = "idle"
    messages: list[Message] = Field(default_factory=list)
    artifacts: dict[str, Any] = Field(default_factory=dict)
    schema_version: str = HARNESS_SCHEMA_VERSION


class ConversationSummary(BaseModel):
    id: str
    title: str
    updated_at: datetime
    status: ConversationStatus
