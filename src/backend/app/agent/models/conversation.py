from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


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
    payload: dict = {}


# Union of all part types
MessagePart = TextPart | ToolCallPart | EventPart


class ConversationMessage(BaseModel):
    id: str
    role: MessageRole
    parts: list[MessagePart]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    token_count: Optional[int] = None          # tokens used by this message
    model: Optional[str] = None                # which LLM generated this


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class Conversation(ConversationSummary):
    messages: list[ConversationMessage] = []
    metadata: dict = {}   # arbitrary metadata (e.g. linked project, node_id)
