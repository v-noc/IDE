
import uuid
import logging

from app.agent.conversation_store import ConversationStore
from app.agent.llm.gateway import LLMGateway
from app.agent.runner.task_manager import TaskManager
from app.agent.service.title_generator import generate_conversation_title
from app.agent.workflows.base import BaseWorkflow
from app.core.model.conversation_domain import (
    ConversationMessage,
    TaskPart,
    TextPart,
)
from app.core.model.conversation_enums import (
    MessageRole,
    TaskState as ConversationTaskState,
)
from app.core.model.conversation_nodes import Task

logger = logging.getLogger(__name__)


class WorkflowService:
    def __init__(
        self,
        task_manager: TaskManager,
        llm_gateway: LLMGateway,
    ):
        self._tasks = task_manager
        self._llm = llm_gateway
        self._task_part_cache: dict[str, TaskPart] = {}

    @property
    def llm_factory(self):
        return self._llm.factory

    async def run(
        self,
        workflow: BaseWorkflow,
        *,
        store: ConversationStore,
        conversation_id: str | None = None,
        **params,
    ) -> tuple[str, str]:
        # 1. Ensure conversation exists
        if conversation_id is None:
            title, desc = await generate_conversation_title(
                self._llm, workflow, params
            )
            conversation_id = await store.create_conversation(
                title, desc
            )

        # 2. Forward-declare task_id so the callback can close over it
        task_id_holder: list[str] = []

        async def _on_status(status: Task) -> None:
            if task_id_holder:
                await self._sync_task_part(
                    store, conversation_id, task_id_holder[0], status
                )

        # 3. Submit
        task_id = self._tasks.submit(
            name=f"workflow:{workflow.name}",
            coro_factory=workflow.run,
            on_status_update=_on_status,
            **params,
        )
        task_id_holder.append(task_id)

        # 4. Write timeline message
        task_part = TaskPart(
            task_id=task_id,
            title=f"{workflow.name}: {params.get('node_id', '')}",
            workflow_name=workflow.name,
            workflow_params=params,
        )
        await store.add_message(
            conversation_id,
            ConversationMessage(
                id=str(uuid.uuid4()),
                role=MessageRole.ASSISTANT,
                parts=[
                    TextPart(text=f"Starting {workflow.name}..."),
                    task_part,
                ],
            ),
        )
        self._task_part_cache[task_id] = task_part

        # 5. Push initial state
        initial = self._tasks.get_status(task_id)
        await self._sync_task_part(
            store, conversation_id, task_id, initial
        )

        return conversation_id, task_id

    async def _sync_task_part(
        self,
        store: ConversationStore,
        conversation_id: str,
        task_id: str,
        status: Task | None,
    ) -> None:
        if status is None:
            return
        base = self._task_part_cache.get(
            task_id, TaskPart(task_id=task_id, title=status.name)
        )
        updated = base.model_copy(
            update={
                "state": ConversationTaskState(status.state.value),
                "progress": status.progress,
                "description": status.progress_message or "",
                "started_at": status.started_at,
                "finished_at": status.finished_at,
            }
        )
        await store.upsert_task_part(conversation_id, updated)
        self._task_part_cache[task_id] = updated
