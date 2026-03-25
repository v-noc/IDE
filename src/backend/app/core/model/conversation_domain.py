"""Conversation UI/message models (parts, messages, aggregates)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field

from app.core.model.conversation_enums import MessageRole, TaskState
from app.core.model.conversation_nodes import ConversationNode, SubTask


class TextPart(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ToolCallPart(BaseModel):
    """Agent-side tool call record (not shown to user directly)."""
    type: Literal["tool_call"] = "tool_call"
    tool_name: str
    tool_input: dict
    tool_output: Optional[str] = None


class EventPart(BaseModel):
    """Replay event (mirrors frontend ReplayEvent)."""
    type: Literal["event"] = "event"
    at: int
    event_type: str        # "wait" | "click" | "focus"
    payload: dict = Field(default_factory=dict)


class TaskPart(BaseModel):
    """
    Marker in the message timeline for a workflow run.

    Persist a minimal row: ``task_id`` must match the Task document ``@id`` in
    Terminus (e.g. ``TaskSchema/<uuid>``). Title, state, and progress are filled
    when serving messages by loading the linked ``Task`` (see repository hydrate).
    """

    type: Literal["task"] = "task"
    task_id: str
    title: str = ""
    description: str = ""
    state: TaskState = TaskState.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    progress: float = 0.0
    sub_tasks: list[SubTask] = Field(default_factory=list)
    # Mirrors Task.sub_task_count when known; used when sub_tasks are not embedded.
    sub_task_count: int = 0
    touched_node_ids: list[str] = Field(default_factory=list)
    workflow_name: Optional[str] = None
    workflow_params: Optional[dict] = None


MessagePart = Union[TextPart, ToolCallPart, EventPart, TaskPart]


class ConversationMessage(BaseModel):
    id: str
    role: MessageRole
    parts: list[MessagePart]
    sequence: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    token_count: Optional[int] = None
    model: Optional[str] = None


class ConversationSummary(BaseModel):
    id: str
    title: str
    description: str = ""
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    has_active_task: bool = False

    @classmethod
    def from_conversation_node(
        cls, node: ConversationNode
    ) -> "ConversationSummary":
        return cls(
            id=node.id,
            title=node.name,
            description=node.description,
            created_at=node.created_at,
            updated_at=node.updated_at,
            message_count=node.message_count,
            has_active_task=node.has_active_task,
        )


class Conversation(ConversationSummary):
    messages: list[ConversationMessage] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    @classmethod
    def from_conversation_node(
        cls,
        node: ConversationNode,
        *,
        messages: list[ConversationMessage],
        metadata: dict,
    ) -> "Conversation":
        summary = ConversationSummary.from_conversation_node(node)
        return cls(
            **summary.model_dump(),
            messages=messages,
            metadata=metadata,
        )
