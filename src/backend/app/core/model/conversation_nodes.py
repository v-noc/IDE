"""Pydantic shapes for agent conversation / message / task documents stored in TerminusDB."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


class ConversationNode(BaseModel):
    id: str
    name: str
    description: str = ""
    metadata_json: str = "{}"
    message_count: int = 0
    has_active_task: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @staticmethod
    def from_raw_dict(raw_dict: dict[str, Any]) -> "MessageNode":
        conv = raw_dict.get("conversation")
        conv_id = conv if isinstance(conv, str) else (conv or {}).get("@id", "")
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


class TaskNode(BaseModel):
    id: str
    name: str
    description: str = ""
    conversation_id: str = ""
    message_id: str = ""
    state: str = "pending"
    progress: float = 0.0
    progress_message: str = ""
    workflow_name: Optional[str] = None
    workflow_params_json: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    result_json: Optional[str] = None
    sub_task_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @staticmethod
    def from_raw_dict(raw_dict: dict[str, Any]) -> "TaskNode":
        conv = raw_dict.get("conversation")
        msg = raw_dict.get("message")
        conv_id = conv if isinstance(conv, str) else (conv or {}).get("@id", "")
        msg_id = msg if isinstance(msg, str) else (msg or {}).get("@id", "")
        return TaskNode(
            id=raw_dict["@id"],
            name=raw_dict["name"],
            description=raw_dict.get("description") or "",
            conversation_id=conv_id or "",
            message_id=msg_id or "",
            state=raw_dict.get("state") or "pending",
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


class SubTaskNode(BaseModel):
    id: str
    task_id: str
    name: str
    description: str = ""
    state: str = "pending"
    sequence: int = 0
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    touched_node_ids_json: str = "[]"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @staticmethod
    def from_raw_dict(raw_dict: dict[str, Any]) -> "SubTaskNode":
        parent = raw_dict.get("task")
        task_id = parent if isinstance(parent, str) else (parent or {}).get("@id", "")
        return SubTaskNode(
            id=raw_dict["@id"],
            task_id=task_id or "",
            name=raw_dict["name"],
            description=raw_dict.get("description") or "",
            state=raw_dict.get("state") or "pending",
            sequence=int(raw_dict.get("sequence") or 0),
            started_at=raw_dict.get("started_at"),
            finished_at=raw_dict.get("finished_at"),
            error=raw_dict.get("error"),
            touched_node_ids_json=raw_dict.get("touched_node_ids_json") or "[]",
            created_at=raw_dict["created_at"],
            updated_at=raw_dict["updated_at"],
        )


def _raw_bool(value: Any) -> bool:
    if value is True or value is False:
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)
