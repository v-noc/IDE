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


def task_document_lookup_ids(task_id: str) -> list[str]:
    """
    Terminus task document ids may be stored as `TaskSchema/<uuid>` while clients
    sometimes pass a bare UUID. Return candidates to try with get_document / WOQL.
    """
    s = (task_id or "").strip()
    if not s:
        return []
    out: list[str] = []
    if "/" in s:
        out.append(s)
        tail = terminus_doc_id_tail(s)
        prefixed = f"TaskSchema/{tail}" if tail else ""
        if prefixed and prefixed not in out:
            out.append(prefixed)
    else:
        out.append(f"TaskSchema/{s}")
        out.append(s)
    seen: set[str] = set()
    ordered: list[str] = []
    for x in out:
        if x not in seen:
            seen.add(x)
            ordered.append(x)
    return ordered


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
