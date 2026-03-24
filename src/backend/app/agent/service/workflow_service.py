# app/agent/service/workflow_service.py

from __future__ import annotations

import uuid
import logging
from typing import Any

from app.agent.conversation_store import ConversationStore
from app.agent.llm.gateway import LLMGateway
from app.agent.runner.task_context import TaskContext
from app.agent.runner.task_manager import TaskManager
from app.agent.runner.task_persistence import TaskPersistence
from app.agent.service.title_generator import (
    generate_conversation_title,
)
from app.agent.workflows.base import BaseWorkflow
from app.core.model.conversation_domain import (
    ConversationMessage,
    TaskPart,
    TextPart,
)
from app.core.model.conversation_enums import (
    MessageRole,
    TaskState,
    TaskState as ConversationTaskState,
)
from app.core.model.conversation_nodes import Task

logger = logging.getLogger(__name__)

_TERMINAL_STATES = {
    TaskState.COMPLETED,
    TaskState.FAILED,
    TaskState.CANCELLED,
}


class WorkflowService:
    def __init__(
        self,
        task_manager: TaskManager,
        llm_gateway: LLMGateway,
        db_client: Any = None,
    ):
        self._tasks = task_manager
        self._llm = llm_gateway
        self._db_client = db_client
        self._task_part_cache: dict[str, TaskPart] = {}
        # Keep reference to TaskContext per task_id so the
        # status callback can read subtask snapshots.
        self._task_contexts: dict[str, TaskContext] = {}

    @property
    def llm_factory(self):
        return self._llm.factory

    async def join_task(self, task_id: str) -> None:
        await self._tasks.join(task_id)

    # -- single workflow --------------------------------------------------

    async def run(
        self,
        workflow: BaseWorkflow,
        *,
        store: ConversationStore,
        conversation_id: str | None = None,
        **params,
    ) -> tuple[str, str]:
        workflow_params = dict(params)
        wf_title = workflow_params.pop("conversation_title", None)
        wf_desc = workflow_params.pop(
            "conversation_description", None
        )

        # 1. Ensure conversation
        if conversation_id is None:
            gen_title, gen_desc = await generate_conversation_title(
                self._llm, workflow, workflow_params
            )
            title = (wf_title or "").strip() or gen_title
            desc = (wf_desc or "").strip() or gen_desc
            conversation_id = await store.create_conversation(
                title, desc
            )

        # 2. Write timeline message with TaskPart (id must match TaskManager)
        message_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())

        task_part = TaskPart(
            task_id=task_id,
            title=(
                f"{workflow.name}: "
                f"{workflow_params.get('node_id', '')}"
            ),
            workflow_name=workflow.name,
            workflow_params=workflow_params,
        )
        await store.add_message(
            conversation_id,
            ConversationMessage(
                id=message_id,
                role=MessageRole.ASSISTANT,
                parts=[
                    TextPart(
                        text=f"Starting {workflow.name}..."
                    ),
                    task_part,
                ],
            ),
        )

        # 3. Create TaskContext (WorkflowService owns it)
        ctx = TaskContext()
        task_id_holder: list[str] = []

        async def _on_status(status: Task) -> None:
            if not task_id_holder:
                return
            task_id = task_id_holder[0]
            subtask_snapshots = ctx.subtask_snapshots
            await self._sync_task_part(
                store,
                conversation_id,
                task_id,
                status,
                subtask_snapshots,
            )
            # On terminal state → flush to DB
            if status.state in _TERMINAL_STATES:
                await self._flush_to_db(
                    task_id=task_id,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    status=status,
                    ctx=ctx,
                    workflow=workflow,
                    workflow_params=workflow_params,
                )

        # 4. Submit — TaskManager runs workflow.run() in background
        # Do not let client params override the runner task_id.
        submit_kw = {
            k: v for k, v in workflow_params.items() if k != "task_id"
        }
        self._tasks.submit(
            name=f"workflow:{workflow.name}",
            coro_factory=workflow.run,
            on_status_update=_on_status,
            task_context=ctx,
            task_id=task_id,
            **submit_kw,
        )
        task_id_holder.append(task_id)
        self._task_contexts[task_id] = ctx

        # 5. Prime cache / confirm TaskPart row (message already has task_id)
        self._task_part_cache[task_id] = task_part
        await store.upsert_task_part(conversation_id, task_part)

        # 6. Persist Task document to DB immediately (PENDING)
        await self._create_task_in_db(
            task_id=task_id,
            conversation_id=conversation_id,
            message_id=message_id,
            workflow=workflow,
            workflow_params=workflow_params,
        )

        # 7. Push initial state
        initial = self._tasks.get_status(task_id)
        if initial:
            await self._sync_task_part(
                store, conversation_id, task_id, initial, []
            )

        return conversation_id, task_id

    # -- batch (non-blocking) ---------------------------------------------

    async def run_batch(
        self,
        steps: list[dict[str, Any]],
        *,
        workflow_factory: Any,
        store: ConversationStore,
        conversation_id: str | None = None,
        conversation_title: str | None = None,
        conversation_description: str | None = None,
    ) -> tuple[str, str]:
        """
        Submit an entire batch as ONE background task.
        Steps run sequentially inside the background task.
        Returns immediately with (conversation_id, parent_task_id).
        """
        if conversation_id is None:
            title = (
                (conversation_title or "").strip()
                or "Batch workflow"
            )
            desc = (
                (conversation_description or "").strip()
                or "Running multiple workflow steps"
            )
            conversation_id = await store.create_conversation(
                title, desc
            )

        message_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        task_part = TaskPart(
            task_id=task_id,
            title="Batch workflow",
            workflow_name="batch",
            workflow_params={"step_count": len(steps)},
        )
        await store.add_message(
            conversation_id,
            ConversationMessage(
                id=message_id,
                role=MessageRole.ASSISTANT,
                parts=[
                    TextPart(text="Starting batch workflow..."),
                    task_part,
                ],
            ),
        )

        ctx = TaskContext()
        task_id_holder: list[str] = []

        async def _on_status(status: Task) -> None:
            if not task_id_holder:
                return
            tid = task_id_holder[0]
            await self._sync_task_part(
                store,
                conversation_id,
                tid,
                status,
                ctx.subtask_snapshots,
            )
            if status.state in _TERMINAL_STATES:
                await self._flush_to_db(
                    task_id=tid,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    status=status,
                    ctx=ctx,
                    workflow=None,
                    workflow_params={
                        "step_count": len(steps)
                    },
                )

        async def _batch_runner(
            task_status: Task | None = None,
            task_context: TaskContext | None = None,
            **_kw,
        ):
            effective_ctx = task_context or TaskContext.noop()
            if task_status:
                effective_ctx.bind(task_status)

            results = []
            total = len(steps)
            for i, step in enumerate(steps):
                wf = workflow_factory(step)
                st = effective_ctx.subtask(
                    name=f"{wf.name}",
                    subtask_id=f"step-{i}-{wf.name}",
                )
                st.start(
                    f"Running {wf.name} ({i + 1}/{total})"
                )
                try:
                    # Each step gets its own nested context
                    step_ctx = TaskContext.noop()
                    result = await wf.execute(
                        step_ctx, **step["params"]
                    )
                    results.append(result)
                    st.complete(f"Completed {wf.name}")
                except Exception as exc:
                    st.fail(str(exc))
                    raise

            return {"batch_results": results}

        self._tasks.submit(
            name="workflow:batch",
            coro_factory=_batch_runner,
            on_status_update=_on_status,
            task_context=ctx,
            task_id=task_id,
        )
        task_id_holder.append(task_id)
        self._task_contexts[task_id] = ctx

        self._task_part_cache[task_id] = task_part
        await store.upsert_task_part(conversation_id, task_part)

        await self._create_task_in_db(
            task_id=task_id,
            conversation_id=conversation_id,
            message_id=message_id,
            workflow=None,
            workflow_params={"step_count": len(steps)},
            name="workflow:batch",
        )

        return conversation_id, task_id

    # -- DB persistence ---------------------------------------------------

    async def _create_task_in_db(
        self,
        *,
        task_id: str,
        conversation_id: str,
        message_id: str,
        workflow: BaseWorkflow | None,
        workflow_params: dict,
        name: str | None = None,
    ) -> None:
        if not self._db_client:
            return
        import json

        persistence = TaskPersistence(self._db_client)
        task_doc = Task(
            id=task_id,
            name=name or f"workflow:{workflow.name}" if workflow else "workflow:batch",
            conversation_id=conversation_id,
            message_id=message_id,
            state=TaskState.PENDING,
            workflow_name=workflow.name if workflow else "batch",
            workflow_params_json=json.dumps(
                workflow_params, default=str
            ),
        )
        try:
            await persistence.create_task(task_doc)
        except Exception:
            logger.exception(
                "Failed to persist task %s to DB", task_id
            )

    async def _flush_to_db(
        self,
        *,
        task_id: str,
        conversation_id: str,
        message_id: str,
        status: Task,
        ctx: TaskContext,
        workflow: BaseWorkflow | None,
        workflow_params: dict,
    ) -> None:
        if not self._db_client:
            return

        persistence = TaskPersistence(self._db_client)

        try:
            await persistence.update_task_state(
                task_id,
                state=status.state,
                progress=status.progress,
                progress_message=status.progress_message,
                error=status.error,
                result_json=status.result_json,
                started_at=status.started_at,
                finished_at=status.finished_at,
                sub_task_count=ctx.subtask_count,
            )
        except Exception:
            logger.exception(
                "Failed to update task %s in DB", task_id
            )

        try:
            await persistence.flush_subtasks(
                task_id, ctx.subtask_snapshots
            )
        except Exception:
            logger.exception(
                "Failed to flush subtasks for task %s", task_id
            )

        # Cleanup
        self._task_contexts.pop(task_id, None)
        self._task_part_cache.pop(task_id, None)

    # -- TaskPart sync (frontend updates) ---------------------------------

    async def _sync_task_part(
        self,
        store: ConversationStore,
        conversation_id: str,
        task_id: str,
        status: Task | None,
        subtask_snapshots: list | None = None,
    ) -> None:
        if status is None:
            return
        base = self._task_part_cache.get(
            task_id,
            TaskPart(task_id=task_id, title=status.name),
        )
        updated = base.model_copy(
            update={
                "state": ConversationTaskState(
                    status.state.value
                ),
                "progress": status.progress,
                "description": status.progress_message or "",
                "started_at": status.started_at,
                "finished_at": status.finished_at,
            }
        )
        await store.upsert_task_part(conversation_id, updated)
        self._task_part_cache[task_id] = updated
