import asyncio
import uuid
from datetime import datetime
from typing import Any, Callable, Optional

from app.agent.models.task_status import TaskStatus, TaskState


class TaskManager:

    def __init__(self):
        self._tasks: dict[str, TaskStatus] = {}
        self._asyncio_tasks: dict[str, asyncio.Task] = {}

    def submit(
        self,
        name: str,
        coro_factory: Callable[..., Any],
        on_status_update: Optional[Callable[[TaskStatus], None]] = None,
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

        update_interval_s = 0.5
        def _emit_status_update():
            if not on_status_update:
                return
            try:
                on_status_update(status.model_copy(deep=True))
            except Exception:
                # Status propagation should never crash task execution.
                return

        async def _wrapper():
            status.state = TaskState.RUNNING
            status.started_at = datetime.utcnow()
            _emit_status_update()

            reporter_task = None
            if on_status_update:
                async def _reporter():
                    while status.state == TaskState.RUNNING:
                        _emit_status_update()
                        await asyncio.sleep(update_interval_s)

                reporter_task = asyncio.create_task(_reporter())

            try:
                run_kwargs = dict(kwargs)
                run_kwargs.setdefault("task_status", status)
                result = await coro_factory(**run_kwargs)
                status.state = TaskState.COMPLETED
                status.result = result
            except asyncio.CancelledError:
                status.state = TaskState.CANCELLED
            except Exception as e:
                status.state = TaskState.FAILED
                status.error = str(e)
            finally:
                status.finished_at = datetime.utcnow()
                if reporter_task:
                    reporter_task.cancel()
                    try:
                        await reporter_task
                    except asyncio.CancelledError:
                        pass
                _emit_status_update()

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
