# app/agent/runner/task_context.py

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from app.core.model.conversation_enums import TaskState
from app.core.model.conversation_nodes import Task


class SubtaskHandle:
    """Lightweight handle for a single subtask."""

    def __init__(self, subtask: Task, parent: TaskContext):
        self._subtask = subtask
        self._parent = parent

    @property
    def id(self) -> str:
        return self._subtask.id

    def start(self, message: str = "") -> None:
        self._subtask.state = TaskState.RUNNING
        self._subtask.started_at = datetime.now(timezone.utc)
        if message:
            self._subtask.progress_message = message
        self._parent._recompute_progress()

    def update(self, progress: float, message: str = "") -> None:
        self._subtask.progress = max(0.0, min(1.0, progress))
        if message:
            self._subtask.progress_message = message
        self._parent._recompute_progress()

    def complete(self, message: str = "") -> None:
        self._subtask.state = TaskState.COMPLETED
        self._subtask.progress = 1.0
        self._subtask.finished_at = datetime.now(timezone.utc)
        if message:
            self._subtask.progress_message = message
        self._parent._recompute_progress()

    def fail(self, error: str) -> None:
        self._subtask.state = TaskState.FAILED
        self._subtask.error = error
        self._subtask.finished_at = datetime.now(timezone.utc)
        self._parent._recompute_progress()


class TaskContext:
    """
    The *only* interface workflows use to report progress.

    Replaces direct mutation of `Task` fields inside workflow code.
    """

    def __init__(self, task: Task):
        self._task = task

    # -- progress helpers -------------------------------------------------

    def update_progress(self, progress: float, message: str = "") -> None:
        """Set progress directly (useful when there are no subtasks)."""
        self._task.progress = max(0.0, min(1.0, progress))
        if message:
            self._task.progress_message = message

    def _recompute_progress(self) -> None:
        if self._task.subtasks:
            self._task.progress = self._task.computed_progress

    # -- subtask management -----------------------------------------------

    def subtask(self, name: str, subtask_id: str | None = None) -> SubtaskHandle:
        sid = subtask_id or str(uuid.uuid4())
        st = Task(
            id=sid,
            parent_id=self._task.id,
            name=name,
            state=TaskState.PENDING,
            created_at=datetime.now(timezone.utc),
        )
        self._task.subtasks.append(st)
        return SubtaskHandle(st, self)

    @property
    def task_snapshot(self) -> Task:
        return self._task.model_copy(deep=True)

    # -- noop context for tests / optional usage --------------------------

    @classmethod
    def noop(cls) -> TaskContext:
        """Context that silently accepts all updates."""
        dummy = Task(
            id="noop",
            name="noop",
            created_at=datetime.now(timezone.utc),
        )
        return cls(dummy)
