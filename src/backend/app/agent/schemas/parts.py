from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field


class TextPart(BaseModel):
    type: Literal["text"] = "text"
    text: str


class NodeRefPart(BaseModel):
    type: Literal["node_ref"] = "node_ref"
    node_id: str
    name: str
    qname: str | None = None
    node_type: str


class DecisionPart(BaseModel):
    type: Literal["decision"] = "decision"
    tool_call_id: str
    decision: Literal["approve", "cancel"]
    overrides: dict[str, Any] = Field(default_factory=dict)


class ReasoningPart(BaseModel):
    type: Literal["reasoning"] = "reasoning"
    origin: Literal["native", "summary"]
    text: str
    duration_ms: int | None = None


class ToolEstimate(BaseModel):
    items: int
    llm_calls: int
    label: str
    over_cap: bool
    knobs: dict[str, Any] = Field(default_factory=dict)


class ToolProgress(BaseModel):
    done: int
    total: int
    label: str


class ArtifactRef(BaseModel):
    doc: str
    render: str


class ToolPending(BaseModel):
    status: Literal["pending"] = "pending"
    input: dict[str, Any]


class ToolAwaitingConfirmation(BaseModel):
    status: Literal["awaiting_confirmation"] = "awaiting_confirmation"
    input: dict[str, Any]
    estimate: ToolEstimate
    knobs: dict[str, Any] = Field(default_factory=dict)


class ToolRunning(BaseModel):
    status: Literal["running"] = "running"
    input: dict[str, Any]
    progress: ToolProgress | None = None
    started_at: datetime


class ToolCompleted(BaseModel):
    status: Literal["completed"] = "completed"
    input: dict[str, Any]
    result: dict[str, Any]
    artifact: ArtifactRef | None = None
    degraded: bool = False
    duration_ms: int


class ToolError(BaseModel):
    status: Literal["error"] = "error"
    input: dict[str, Any]
    error: str
    duration_ms: int


ToolState = Annotated[
    ToolPending
    | ToolAwaitingConfirmation
    | ToolRunning
    | ToolCompleted
    | ToolError,
    Field(discriminator="status"),
]


class ToolPart(BaseModel):
    type: Literal["tool"] = "tool"
    tool_call_id: str
    tool: str
    state: ToolState


Part = Annotated[
    TextPart | NodeRefPart | ReasoningPart | ToolPart | DecisionPart,
    Field(discriminator="type"),
]
