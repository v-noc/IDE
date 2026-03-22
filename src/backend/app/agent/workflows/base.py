from abc import ABC, abstractmethod
from typing import Any

from app.agent.runner.task_context import TaskContext
from app.core.model.conversation_nodes import Task


class BaseWorkflow(ABC):
    """
    Abstract base for all workflows.

    Subclasses implement `execute()`.  The framework calls `run()`,
    which handles TaskContext creation and lifecycle.
    """

    name: str
    description: str

    async def validate(self, **kwargs) -> None:
        """Override to reject invalid params before execution starts."""

    @abstractmethod
    async def execute(self, ctx: TaskContext, **kwargs) -> Any:
        """Implement the workflow logic here."""
        ...

    async def run(self, task_status: Task | None = None, **kwargs) -> Any:
        """
        Template method — called by TaskManager.

        Do NOT override this in subclasses.
        """
        ctx = (
            TaskContext(task_status)
            if task_status
            else TaskContext.noop()
        )
        await self.validate(**kwargs)
        return await self.execute(ctx, **kwargs)
