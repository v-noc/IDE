from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.agent.schemas.conversation import EffortLevel
from app.agent.schemas.parts import Part


class MessageOptions(BaseModel):
    effort: EffortLevel | None = None


class SendMessageRequest(BaseModel):
    parts: list[Part]
    options: MessageOptions | None = None


class DecisionRequest(BaseModel):
    tool_call_id: str
    decision: Literal["approve", "cancel"]
    overrides: dict[str, Any] = Field(default_factory=dict)


class OpenFrame(BaseModel):
    kind: Literal["open"] = "open"
    doc: str
    protocol: int = 2
    snapshot: dict[str, Any]


class PatchFrame(BaseModel):
    kind: Literal["patch"] = "patch"
    doc: str
    seq: int
    ops: list[dict[str, Any]]


class CloseFrame(BaseModel):
    kind: Literal["close"] = "close"
    doc: str
    status: str
    message: str | None = None
