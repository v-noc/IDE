# app/agent/runner/task_persistence.py

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from app.core.model.conversation_enums import TaskState
from app.core.model.conversation_nodes import SubTask, Task
from app.db.async_terminus_client import WOQLQuery as WQ

try:
    from terminusdb_client.woqlquery.woql_query import Doc
except ImportError:  # pragma: no cover
    Doc = dict  # type: ignore

from app.core.model.schemas.conversation_schema import (
    SubTaskSchema,
    TaskSchema,
)

logger = logging.getLogger(__name__)


class TaskPersistence:
    """
    Encapsulates all DB operations for Task and SubTask documents.

    Workflows never touch the DB directly for task tracking.
    """

    def __init__(self, client: Any):
        self._client = client

    # -- Task CRUD --------------------------------------------------------

    async def create_task(self, task: Task) -> str:
        schema = TaskSchema.from_pydantic(task)

        await self._client.insert_document(
            schema,
            commit_msg=f"Create task {task.id}",
        )

        return task.id

    async def update_task_state(
        self,
        task_id: str,
        *,
        state: TaskState,
        progress: float = 0.0,
        progress_message: str = "",
        error: str | None = None,
        result_json: str | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        sub_task_count: int = 0,
    ) -> None:
        now = datetime.now(timezone.utc)
        updates: list = []

        field_map = {
            "state": state.value,
            "progress": progress,
            "progress_message": progress_message,
            "sub_task_count": sub_task_count,
            "updated_at": now,
        }
        if error is not None:
            field_map["error"] = error
        if result_json is not None:
            field_map["result_json"] = result_json
        if started_at is not None:
            field_map["started_at"] = started_at
        if finished_at is not None:
            field_map["finished_at"] = finished_at

        for field, value in field_map.items():
            var = f"v:old_{field}"
            updates.extend(
                [
                    WQ().opt(
                        WQ()
                        .triple(task_id, field, var)
                        .delete_triple(task_id, field, var)
                    ),
                    WQ().add_triple(
                        task_id,
                        field,
                        self._woql_value(value),
                    ),
                ]
            )

        if updates:
            await self._client.query(
                WQ().woql_and(*updates),
                commit_msg=f"Update task {task_id} → {state.value}",
            )

    # -- SubTask batch upsert ---------------------------------------------

    async def flush_subtasks(
        self, task_id: str, subtasks: list[SubTask]
    ) -> None:
        if not subtasks:
            return

        documents = []
        for st in subtasks:
            schema = SubTaskSchema.from_pydantic(
                st.model_copy(update={"task_id": task_id})
            )
            raw = schema._obj_to_dict()[0]
            documents.append(raw)

        await self._client.insert_document(
            documents,
            commit_msg=(
                f"Flush {len(subtasks)} subtasks for task {task_id}"
            ),
        )
    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _woql_value(value: Any):
        if isinstance(value, str):
            return WQ().string(value)
        if isinstance(value, bool):
            return WQ().boolean(value)
        if isinstance(value, int):
            return WQ().iri(str(value))  # or integer helper
        if isinstance(value, float):
            return WQ().string(str(value))
        if isinstance(value, datetime):
            return value
        return WQ().string(str(value))
