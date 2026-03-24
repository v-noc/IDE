# app/agent/runner/task_context.py

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from app.core.model.conversation_enums import SubTaskState, TaskState
from app.core.model.conversation_nodes import SubTask, Task


class SubtaskHandle:
    """Lightweight handle a workflow uses to report on one subtask."""

    def __init__(self, subtask: SubTask, parent: TaskContext):
        self._sub = subtask
        self._parent = parent

    @property
    def id(self) -> str:
        return self._sub.id

    def start(self, message: str = "") -> None:
        self._sub.state = SubTaskState.RUNNING
        self._sub.started_at = datetime.now(timezone.utc)
        if message:
            self._sub.description = message
        self._parent._recompute_progress()

    def update(self, message: str = "") -> None:
        if message:
            self._sub.description = message

    def complete(self, message: str = "") -> None:
        self._sub.state = SubTaskState.COMPLETED
        self._sub.finished_at = datetime.now(timezone.utc)
        if message:
            self._sub.description = message
        self._parent._recompute_progress()

    def fail(self, error: str) -> None:
        self._sub.state = SubTaskState.FAILED
        self._sub.error = error
        self._sub.finished_at = datetime.now(timezone.utc)
        self._parent._recompute_progress()


class TaskContext:
    """
    The ONLY interface workflows use to report progress.

    Tracks subtasks in memory. The WorkflowService reads
    snapshots for frontend pushes and final DB flush.
    """

    def __init__(self, task: Task | None = None):
        self._task: Task | None = task
        self._subtasks: list[SubTask] = []
        self._seq = 0

    def bind(self, task: Task) -> None:
        """Bind to the in-memory Task created by TaskManager."""
        self._task = task

    # -- progress ---------------------------------------------------------

    def update_progress(
        self, progress: float, message: str = ""
    ) -> None:
        if self._task:
            self._task.progress = max(0.0, min(1.0, progress))
            if message:
                self._task.progress_message = message

    def _recompute_progress(self) -> None:
        if not self._task or not self._subtasks:
            return
        done = sum(
            1
            for s in self._subtasks
            if s.state
            in {SubTaskState.COMPLETED, SubTaskState.FAILED}
        )
        self._task.progress = done / len(self._subtasks)
        self._task.sub_task_count = len(self._subtasks)

    # -- subtask management -----------------------------------------------

    def subtask(
        self,
        name: str,
        subtask_id: str | None = None,
        touched_node_ids: list[str] | None = None,
    ) -> SubtaskHandle:
        import json

        sid = subtask_id or str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        st = SubTask(
            id=sid,
            task_id=self._task.id if self._task else "",
            name=name,
            state=SubTaskState.PENDING,
            sequence=self._seq,
            touched_node_ids_json=json.dumps(
                touched_node_ids or []
            ),
            created_at=now,
            updated_at=now,
        )
        self._seq += 1
        self._subtasks.append(st)
        self._recompute_progress()
        return SubtaskHandle(st, self)

    # -- snapshots for external consumers ---------------------------------

    @property
    def subtask_snapshots(self) -> list[SubTask]:
        return [s.model_copy(deep=True) for s in self._subtasks]

    @property
    def subtask_count(self) -> int:
        return len(self._subtasks)

    # -- noop for tests / optional ----------------------------------------

    @classmethod
    def noop(cls) -> TaskContext:
        return cls(task=None)
