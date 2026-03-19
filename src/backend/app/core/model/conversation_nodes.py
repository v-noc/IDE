"""Pydantic documents for agent data persisted in TerminusDB (single source types)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

import json

from pydantic import BaseModel, Field, model_validator

from app.core.model.conversation_enums import SubTaskState, TaskState


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _coerce_task_state(value: Any) -> TaskState:
    if isinstance(value, TaskState):
        return value
    try:
        return TaskState(str(value))
    except ValueError:
        return TaskState.PENDING


def _coerce_subtask_state(value: Any) -> SubTaskState:
    if isinstance(value, SubTaskState):
        return value
    try:
        return SubTaskState(str(value))
    except ValueError:
        return SubTaskState.PENDING


class ConversationNode(BaseModel):
    id: str
    name: str
    description: str = ""
    metadata_json: str = "{}"
    message_count: int = 0
    has_active_task: bool = False
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)

    @staticmethod
    def from_raw_dict(raw_dict: dict[str, Any]) -> "ConversationNode":
        return ConversationNode(
            id=raw_dict["@id"],
            name=raw_dict["name"],
            description=raw_dict.get("description") or "",
            metadata_json=raw_dict.get("metadata_json") or "{}",
            message_count=int(raw_dict.get("message_count") or 0),
            has_active_task=_raw_bool(raw_dict.get("has_active_task")),
            created_at=raw_dict["created_at"],
            updated_at=raw_dict["updated_at"],
        )


class MessageNode(BaseModel):
    id: str
    conversation_id: str
    role: str
    parts_json: str
    token_count: Optional[int] = None
    model_name: Optional[str] = None
    sequence: int = 0
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)

    @staticmethod
    def from_raw_dict(raw_dict: dict[str, Any]) -> "MessageNode":
        conv = raw_dict.get("conversation")
        conv_id = (
            conv if isinstance(conv, str) else (conv or {}).get("@id", "")
        )
        return MessageNode(
            id=raw_dict["@id"],
            conversation_id=conv_id or "",
            role=raw_dict["role"],
            parts_json=raw_dict.get("parts_json") or "[]",
            token_count=raw_dict.get("token_count"),
            model_name=raw_dict.get("model_name"),
            sequence=int(raw_dict.get("sequence") or 0),
            created_at=raw_dict["created_at"],
            updated_at=raw_dict["updated_at"],
        )


class TaskDocumentBase(BaseModel):
    """Shared scalar fields for `Task` (persisted workflow run)."""

    id: str = ""
    name: str = ""
    description: str = ""
    conversation_id: str = ""
    message_id: str = ""
    progress: float = 0.0
    progress_message: str = ""
    workflow_name: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    sub_task_count: int = 0
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


class Task(TaskDocumentBase):
    state: TaskState = TaskState.PENDING
    workflow_params_json: Optional[str] = None
    result_json: Optional[str] = None

    @staticmethod
    def from_raw_dict(raw_dict: dict[str, Any]) -> "Task":
        conv = raw_dict.get("conversation")
        msg = raw_dict.get("message")
        conv_id = (
            conv if isinstance(conv, str) else (conv or {}).get("@id", "")
        )
        msg_id = msg if isinstance(msg, str) else (msg or {}).get("@id", "")
        return Task(
            id=raw_dict["@id"],
            name=raw_dict["name"],
            description=raw_dict.get("description") or "",
            conversation_id=conv_id or "",
            message_id=msg_id or "",
            state=_coerce_task_state(raw_dict.get("state")),
            progress=float(raw_dict.get("progress") or 0.0),
            progress_message=raw_dict.get("progress_message") or "",
            workflow_name=raw_dict.get("workflow_name"),
            workflow_params_json=raw_dict.get("workflow_params_json"),
            started_at=raw_dict.get("started_at"),
            finished_at=raw_dict.get("finished_at"),
            error=raw_dict.get("error"),
            result_json=raw_dict.get("result_json"),
            sub_task_count=int(raw_dict.get("sub_task_count") or 0),
            created_at=raw_dict["created_at"],
            updated_at=raw_dict["updated_at"],
        )


class SubTaskDocumentBase(BaseModel):
    """Shared scalar fields for `SubTask` (workflow step under a task)."""

    id: str = ""
    name: str
    description: str = ""
    sequence: int = 0
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


class SubTask(SubTaskDocumentBase):
    task_id: str = ""
    state: SubTaskState = SubTaskState.PENDING
    touched_node_ids_json: str = "[]"

    @model_validator(mode="before")
    @classmethod
    def _legacy_touched_node_ids(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "touched_node_ids" in data:
            data = dict(data)
            data["touched_node_ids_json"] = json.dumps(
                data.pop("touched_node_ids", [])
            )
        return data

    @staticmethod
    def from_raw_dict(raw_dict: dict[str, Any]) -> "SubTask":
        parent = raw_dict.get("task")
        task_id = (
            parent
            if isinstance(parent, str)
            else (parent or {}).get("@id", "")
        )
        return SubTask(
            id=raw_dict["@id"],
            task_id=task_id or "",
            name=raw_dict["name"],
            description=raw_dict.get("description") or "",
            state=_coerce_subtask_state(raw_dict.get("state")),
            sequence=int(raw_dict.get("sequence") or 0),
            started_at=raw_dict.get("started_at"),
            finished_at=raw_dict.get("finished_at"),
            error=raw_dict.get("error"),
            touched_node_ids_json=(
                raw_dict.get("touched_node_ids_json") or "[]"
            ),
            created_at=raw_dict["created_at"],
            updated_at=raw_dict["updated_at"],
        )


def _raw_bool(value: Any) -> bool:
    if value is True or value is False:
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)
