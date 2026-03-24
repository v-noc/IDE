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


def terminus_doc_id_tail(doc_id: str) -> str:
    """Segment after the last `/`, or the full string (bare ids, URLs)."""
    s = (doc_id or "").strip()
    if not s:
        return s
    return s.rsplit("/", 1)[-1]


def terminus_ids_match(a: str, b: str) -> bool:
    """
    True if two Terminus document ids refer to the same document.

    TerminusDB uses `ClassName/<uuid>` while in-memory code often holds
    bare UUIDs; message parts and API payloads may use either form.
    """
    if a == b:
        return True
    if not a or not b:
        return False
    return terminus_doc_id_tail(a) == terminus_doc_id_tail(b)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def parts_to_json(parts: list[MessagePart]) -> str:
    return MESSAGE_PARTS_ADAPTER.dump_json(parts).decode("utf-8")


def parts_from_json(parts_json: str) -> list[MessagePart]:
    return MESSAGE_PARTS_ADAPTER.validate_json(parts_json.encode("utf-8"))
