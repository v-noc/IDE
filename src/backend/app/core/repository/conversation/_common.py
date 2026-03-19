"""Shared helpers and constants for conversation persistence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import TypeAdapter

from app.core.model.conversation_domain import MessagePart
from app.core.model.conversation_enums import TaskState

MESSAGE_PARTS_ADAPTER = TypeAdapter(list[MessagePart])

TERMINAL_TASK_STATES = frozenset(
    {
        TaskState.COMPLETED,
        TaskState.FAILED,
        TaskState.CANCELLED,
    }
)


def new_doc_id(class_name: str) -> str:
    return f"{class_name}/{uuid.uuid4()}"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def parts_to_json(parts: list[MessagePart]) -> str:
    return MESSAGE_PARTS_ADAPTER.dump_json(parts).decode("utf-8")


def parts_from_json(parts_json: str) -> list[MessagePart]:
    return MESSAGE_PARTS_ADAPTER.validate_json(parts_json.encode("utf-8"))
