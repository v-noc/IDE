from datetime import datetime, timezone

from app.core.model.schemas.task_schema import TaskSchema
from app.core.model.tasks import TaskNode


def test_task_schema_self_link_round_trip():
    child_a = "TaskSchema/child-a"
    child_b = "TaskSchema/child-b"
    blocker = "TaskSchema/blocker-1"
    now = datetime.now(timezone.utc)
    node = TaskNode(
        id="TaskSchema/parent-1",
        key="VN-1",
        name="Parent",
        subtask_ids={child_a, child_b},
        blocked_by_ids={blocker},
        created_at=now,
        updated_at=now,
    )

    schema = TaskSchema.from_pydantic(node)
    assert child_a in schema.subtasks
    assert child_b in schema.subtasks
    assert blocker in schema.blocked_by

    restored = schema.to_pydantic()
    assert restored.subtask_ids == {child_a, child_b}
    assert restored.blocked_by_ids == {blocker}


def test_task_schema_legacy_json_fallback():
    now = datetime.now(timezone.utc)
    raw = {
        "@id": "TaskSchema/legacy-1",
        "name": "Legacy",
        "key": "VN-9",
        "task_type": "task",
        "status": "todo",
        "priority": "none",
        "rank": "U",
        "subtask_ids_json": '["TaskSchema/child-1"]',
        "blocked_by_ids_json": '["TaskSchema/blocker-1"]',
        "anchors_json": "[]",
        "notes_json": "[]",
        "created_at": now,
        "updated_at": now,
    }

    node = TaskNode.from_raw_dict(raw)
    assert node.subtask_ids == {"TaskSchema/child-1"}
    assert node.blocked_by_ids == {"TaskSchema/blocker-1"}

    schema = TaskSchema.from_pydantic(node)
    restored = schema.to_pydantic()
    assert restored.subtask_ids == {"TaskSchema/child-1"}
