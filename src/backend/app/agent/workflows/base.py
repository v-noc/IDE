# app/agent/workflows/base.py

from abc import ABC, abstractmethod
from typing import Any

from app.core.model.conversation_nodes import Task
from app.agent.runner.task_context import TaskContext


class BaseWorkflow(ABC):
    """
    Template Method base for all workflows.

    Subclasses implement `validate()` and `execute()`.
    The framework calls `run()`.
    """

    name: str
    description: str

    async def validate(self, **kwargs) -> None:
        """Override to reject invalid params before execution."""

    @abstractmethod
    async def execute(self, ctx: TaskContext, **kwargs) -> Any:
        """Implement workflow logic here."""
        ...

    async def run(
        self,
        task_status: Task | None = None,
        task_context: TaskContext | None = None,
        **kwargs,
    ) -> Any:
        """
        Template method — called by TaskManager.
        Do NOT override in subclasses.
        """
        ctx = task_context or TaskContext.noop()
        if task_status:
            ctx.bind(task_status)
        await self.validate(**kwargs)
        return await self.execute(ctx, **kwargs)
