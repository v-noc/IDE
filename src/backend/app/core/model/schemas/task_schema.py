import json

import orjson

from app.core.model.tasks import BoardColumn, BoardNode, TaskNode
from .base import BaseSchema


class TaskSchema(BaseSchema):
    """TerminusDB document for tasks.

    Nested collections are stored as JSON strings — same pattern as
    ConversationSchema.messages_json / LogSchema.payload.
    """

    key: str
    task_type: str
    status: str
    priority: str
    rank: str
    labels_json: str = "[]"
    subtask_ids_json: str = "[]"
    blocked_by_ids_json: str = "[]"
    anchors_json: str = "[]"
    notes_json: str = "[]"

    @staticmethod
    def from_pydantic(node: TaskNode) -> "TaskSchema":
        anchors_payload = [a.model_dump(mode="json") for a in node.anchors]
        notes_payload = [n.model_dump(mode="json") for n in node.notes]
        return TaskSchema(
            _id=node.id,
            name=node.name,
            description=node.description,
            key=node.key,
            task_type=node.task_type,
            status=node.status,
            priority=node.priority,
            rank=node.rank,
            labels_json=orjson.dumps(sorted(node.labels)).decode(),
            subtask_ids_json=orjson.dumps(sorted(node.subtask_ids)).decode(),
            blocked_by_ids_json=orjson.dumps(sorted(node.blocked_by_ids)).decode(),
            anchors_json=orjson.dumps(anchors_payload).decode(),
            notes_json=orjson.dumps(notes_payload).decode(),
            created_at=node.created_at,
            updated_at=node.updated_at,
        )

    def to_pydantic(self) -> TaskNode:
        raw_id = self._id
        if isinstance(raw_id, str) and not raw_id.startswith("TaskSchema/"):
            raw_id = f"TaskSchema/{raw_id}"

        labels_data = _loads_json(self.labels_json, [])
        subtask_data = _loads_json(self.subtask_ids_json, [])
        blocked_data = _loads_json(self.blocked_by_ids_json, [])
        anchors_data = _loads_json(self.anchors_json, [])
        notes_data = _loads_json(self.notes_json, [])

        return TaskNode.from_raw_dict(
            {
                "@id": raw_id,
                "name": self.name,
                "description": self.description,
                "key": self.key,
                "task_type": self.task_type,
                "status": self.status,
                "priority": self.priority,
                "rank": self.rank,
                "labels_json": orjson.dumps(labels_data).decode(),
                "subtask_ids_json": orjson.dumps(subtask_data).decode(),
                "blocked_by_ids_json": orjson.dumps(blocked_data).decode(),
                "anchors_json": orjson.dumps(anchors_data).decode(),
                "notes_json": orjson.dumps(notes_data).decode(),
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            },
        )


class BoardSchema(BaseSchema):
    columns_json: str = "[]"
    task_counter: int = 0

    @staticmethod
    def from_pydantic(node: BoardNode) -> "BoardSchema":
        columns_payload = [c.model_dump(mode="json") for c in node.columns]
        return BoardSchema(
            _id=node.id,
            name=node.name,
            description=node.description,
            columns_json=orjson.dumps(columns_payload).decode(),
            task_counter=node.task_counter,
            created_at=node.created_at,
            updated_at=node.updated_at,
        )

    def to_pydantic(self) -> BoardNode:
        raw_id = self._id
        if isinstance(raw_id, str) and not raw_id.startswith("BoardSchema/"):
            raw_id = f"BoardSchema/{raw_id}"

        columns_data = _loads_json(self.columns_json, [])

        return BoardNode.from_raw_dict(
            {
                "@id": raw_id,
                "name": self.name,
                "description": self.description,
                "columns_json": orjson.dumps(columns_data).decode(),
                "task_counter": self.task_counter,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            },
        )


def _loads_json(raw: str, default):
    if not raw:
        return default
    try:
        return orjson.loads(raw)
    except orjson.JSONDecodeError:
        return json.loads(raw)


DEFAULT_COLUMNS = [
    {
        "id": "backlog",
        "title": "Backlog",
        "color": "#6b7280",
        "is_done": False,
        "is_backlog": True,
    },
    {"id": "todo", "title": "To do", "color": "#3b82f6", "is_done": False, "is_backlog": False},
    {
        "id": "in_progress",
        "title": "In progress",
        "color": "#f59e0b",
        "is_done": False,
        "is_backlog": False,
    },
    {
        "id": "in_review",
        "title": "In review",
        "color": "#8b5cf6",
        "is_done": False,
        "is_backlog": False,
    },
    {"id": "done", "title": "Done", "color": "#22c55e", "is_done": True, "is_backlog": False},
]


def default_board_node() -> BoardNode:
    return BoardNode(
        id="BoardSchema/default",
        name="Board",
        description="Project task board",
        columns=[BoardColumn(**c) for c in DEFAULT_COLUMNS],
        task_counter=0,
    )
