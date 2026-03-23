# app/agent/runner/task_manager.py

import asyncio
import inspect
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Optional, Union

from app.core.model.conversation_enums import TaskState
from app.core.model.conversation_nodes import Task

logger = logging.getLogger(__name__)

_STATUS_INTERVAL_S = 0.5


class TaskManager:

    def __init__(self):
        self._tasks: dict[str, Task] = {}
        self._asyncio_tasks: dict[str, asyncio.Task] = {}

    def submit(
        self,
        name: str,
        coro_factory: Callable[..., Any],
        on_status_update: Optional[
            Callable[[Task], Union[None, Any]]
        ] = None,
        **kwargs,
    ) -> str:
        task_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        status = Task(
            id=task_id,
            name=name,
            state=TaskState.PENDING,
            created_at=now,
            updated_at=now,
        )
        self._tasks[task_id] = status

        async def _emit():
            if not on_status_update:
                return
            try:
                out = on_status_update(status.model_copy(deep=True))
                if inspect.isawaitable(out):
                    await out
            except Exception:
                logger.debug("status callback error", exc_info=True)

        async def _wrapper():
            status.state = TaskState.RUNNING
            status.started_at = datetime.now(timezone.utc)
            await _emit()

            reporter: asyncio.Task | None = None
            if on_status_update:

                async def _reporter():
                    while status.state == TaskState.RUNNING:
                        await _emit()
                        await asyncio.sleep(_STATUS_INTERVAL_S)

                reporter = asyncio.create_task(_reporter())

            try:
                run_kwargs = dict(kwargs)
                run_kwargs.setdefault("task_status", status)
                result = await coro_factory(**run_kwargs)
                status.state = TaskState.COMPLETED
                status.result_json = (
                    json.dumps(result, default=str)
                    if result is not None
                    else None
                )
            except asyncio.CancelledError:
                status.state = TaskState.CANCELLED
            except Exception as e:
                status.state = TaskState.FAILED
                status.error = str(e)
                logger.exception("Task %s failed", task_id)
            finally:
                status.finished_at = datetime.now(timezone.utc)
                if reporter:
                    reporter.cancel()
                    try:
                        await reporter
                    except asyncio.CancelledError:
                        pass
                await _emit()

        atask = asyncio.get_running_loop().create_task(_wrapper())
        self._asyncio_tasks[task_id] = atask
        return task_id

    def get_status(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    async def join(self, task_id: str) -> None:
        atask = self._asyncio_tasks.get(task_id)
        if atask:
            await atask

    def cancel(self, task_id: str) -> bool:
        atask = self._asyncio_tasks.get(task_id)
        if atask and not atask.done():
            atask.cancel()
            return True
        return False

    def list_tasks(self) -> list[Task]:
        return list(self._tasks.values())
