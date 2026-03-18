import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Optional

from app.agent.models.task_status import TaskStatus, TaskState


class TaskManager:

    def __init__(self):
        self._tasks: dict[str, TaskStatus] = {}
        self._asyncio_tasks: dict[str, asyncio.Task] = {}

    def submit(
        self,
        name: str,
        coro_factory: Callable[..., Any],
        **kwargs
    ) -> str:
        task_id = str(uuid.uuid4())
        status = TaskStatus(
            id=task_id,
            name=name,
            state=TaskState.PENDING,
            created_at=datetime.utcnow(),
        )
        self._tasks[task_id] = status

        async def _wrapper():
            status.state = TaskState.RUNNING
            status.started_at = datetime.utcnow()
            try:
                result = await coro_factory(**kwargs)
                status.state = TaskState.COMPLETED
                status.result = result
            except asyncio.CancelledError:
                status.state = TaskState.CANCELLED
            except Exception as e:
                status.state = TaskState.FAILED
                status.error = str(e)
            finally:
                status.finished_at = datetime.utcnow()

        loop = asyncio.get_running_loop()
        atask = loop.create_task(_wrapper())
        self._asyncio_tasks[task_id] = atask
        return task_id

    def get_status(self, task_id: str) -> Optional[TaskStatus]:
        return self._tasks.get(task_id)

    def cancel(self, task_id: str) -> bool:
        atask = self._asyncio_tasks.get(task_id)
        if atask and not atask.done():
            atask.cancel()
            return True
        return False

    def list_tasks(self) -> list[TaskStatus]:
        return list(self._tasks.values())
