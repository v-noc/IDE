from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

TaskType = Literal["epic", "task", "bug", "improvement"]
TaskPriority = Literal["none", "low", "medium", "high", "urgent"]
NoteOrigin = Literal["system", "user"]
NodeKind = Literal["function", "class", "file", "folder", "call"]


class TaskAnchor(BaseModel):
    node_id: str
    qname: str
    kind: str


class TaskNote(BaseModel):
    text: str
    at: datetime
    origin: NoteOrigin = "user"


class TaskNode(BaseModel):
    id: str
    key: str
    name: str
    description: str = ""
    task_type: TaskType = "task"
    status: str = "backlog"
    priority: TaskPriority = "none"
    labels: set[str] = Field(default_factory=set)
    rank: str = "U"
    subtask_ids: set[str] = Field(default_factory=set)
    blocked_by_ids: set[str] = Field(default_factory=set)
    anchors: list[TaskAnchor] = Field(default_factory=list)
    notes: list[TaskNote] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @staticmethod
    def from_raw_dict(raw_dict: dict[str, Any]) -> TaskNode:
        import orjson

        labels = _parse_id_set(
            raw_dict.get("labels_json") or raw_dict.get("labels"),
        )
        subtask_ids = _parse_id_set(raw_dict.get("subtasks"))
        if not subtask_ids:
            subtask_ids = _parse_id_set(
                raw_dict.get("subtask_ids_json")
                or raw_dict.get("subtask_ids"),
            )
        blocked_by_ids = _parse_id_set(raw_dict.get("blocked_by"))
        if not blocked_by_ids:
            blocked_by_ids = _parse_id_set(
                raw_dict.get("blocked_by_ids_json")
                or raw_dict.get("blocked_by_ids"),
            )

        anchors_raw = raw_dict.get("anchors_json") or raw_dict.get("anchors") or "[]"
        if isinstance(anchors_raw, str):
            anchors_data = orjson.loads(anchors_raw) if anchors_raw else []
        else:
            anchors_data = anchors_raw

        notes_raw = raw_dict.get("notes_json") or raw_dict.get("notes") or "[]"
        if isinstance(notes_raw, str):
            notes_data = orjson.loads(notes_raw) if notes_raw else []
        else:
            notes_data = notes_raw

        raw_id = raw_dict.get("@id") or raw_dict.get("id", "")
        if isinstance(raw_id, str) and not raw_id.startswith("TaskSchema/"):
            raw_id = f"TaskSchema/{raw_id}"

        return TaskNode(
            id=raw_id,
            key=raw_dict.get("key", ""),
            name=raw_dict.get("name", ""),
            description=raw_dict.get("description", ""),
            task_type=raw_dict.get("task_type", "task"),
            status=raw_dict.get("status", "backlog"),
            priority=raw_dict.get("priority", "none"),
            labels=labels,
            rank=raw_dict.get("rank", "U"),
            subtask_ids=subtask_ids,
            blocked_by_ids=blocked_by_ids,
            anchors=[TaskAnchor(**a) for a in anchors_data],
            notes=[TaskNote(**n) for n in notes_data],
            created_at=raw_dict.get("created_at", datetime.now(timezone.utc)),
            updated_at=raw_dict.get("updated_at", datetime.now(timezone.utc)),
        )


def _parse_id_set(raw) -> set[str]:
    if raw is None:
        return set()
    if isinstance(raw, str):
        import orjson

        raw = orjson.loads(raw) if raw else []
    if isinstance(raw, set):
        return raw
    if isinstance(raw, list):
        return {
            s if isinstance(s, str) else s.get("@id", s.get("id", ""))
            for s in raw
            if s
        }
    return set()


class BoardColumn(BaseModel):
    id: str
    title: str
    color: str
    is_done: bool = False
    is_backlog: bool = False


class BoardNode(BaseModel):
    id: str
    name: str = "Board"
    description: str = ""
    columns: list[BoardColumn] = Field(default_factory=list)
    task_counter: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @staticmethod
    def from_raw_dict(raw_dict: dict[str, Any]) -> BoardNode:
        import orjson

        columns_raw = raw_dict.get("columns_json") or raw_dict.get("columns") or "[]"
        if isinstance(columns_raw, str):
            columns_data = orjson.loads(columns_raw) if columns_raw else []
        else:
            columns_data = columns_raw

        raw_id = raw_dict.get("@id") or raw_dict.get("id", "")
        if isinstance(raw_id, str) and not raw_id.startswith("BoardSchema/"):
            raw_id = f"BoardSchema/{raw_id}"

        return BoardNode(
            id=raw_id,
            name=raw_dict.get("name", "Board"),
            description=raw_dict.get("description", ""),
            columns=[
                BoardColumn(
                    **{
                        **c,
                        "is_backlog": c.get(
                            "is_backlog",
                            c.get("id") == "backlog",
                        ),
                    },
                )
                for c in columns_data
            ],
            task_counter=raw_dict.get("task_counter", 0),
            created_at=raw_dict.get("created_at", datetime.now(timezone.utc)),
            updated_at=raw_dict.get("updated_at", datetime.now(timezone.utc)),
        )
