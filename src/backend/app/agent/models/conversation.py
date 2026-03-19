from pydantic import BaseModel, Field
from typing import Optional, Literal, Union
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
    payload: dict = Field(default_factory=dict)


class SubTaskState(str, Enum):
    PENDING = "pending"       # ○  not started
    RUNNING = "running"       # ●  in progress
    COMPLETED = "completed"   # ✓  done
    FAILED = "failed"         # ✗  error
    SKIPPED = "skipped"       # —  skipped


class SubTask(BaseModel):
    """One step in a task's timeline."""
    id: str
    name: str                          # e.g. "parse_imports.py"
    description: str = ""
    state: SubTaskState = SubTaskState.PENDING
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    # TerminusDB node IDs modified by this step
    touched_node_ids: list[str] = Field(default_factory=list)


class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPart(BaseModel):
    """
    A task embedded inside a conversation message.
    Expands into a sub-task timeline with status + touched nodes.
    """

    type: Literal["task"] = "task"
    task_id: str
    title: str
    description: str = ""
    state: TaskState = TaskState.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    progress: float = 0.0
    sub_tasks: list[SubTask] = Field(default_factory=list)
    touched_node_ids: list[str] = Field(default_factory=list)
    workflow_name: Optional[str] = None
    workflow_params: Optional[dict] = None


# Union of all part types
MessagePart = Union[TextPart, ToolCallPart, EventPart, TaskPart]


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
    description: str = ""                 # LLM-generated summary
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    has_active_task: bool = False          # quick flag for UI


class Conversation(ConversationSummary):
    messages: list[ConversationMessage] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
