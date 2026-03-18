# agent/runner/executor.py

from agent.runner.task_manager import TaskManager
from agent.graph.builder import build_agent_graph
from agent.workflows.base import BaseWorkflow
from app.agent.models.conversation import ConversationMessage, MessageRole, SubTask, TaskPart, TextPart


class AgentExecutor:
    """High-level entry point for running agents and workflows as tasks."""

    def __init__(
        self,
        task_manager: TaskManager,
        llm_factory,
        conversation_store,
    ):
        self.task_manager = task_manager
        self.llm_factory = llm_factory
        self.store = conversation_store

    async def run_workflow(
        self,
        workflow: BaseWorkflow,
        conversation_id: str | None = None,
        **kwargs,
    ) -> tuple[str, str]:
        """
        Submit a workflow for background execution.
        If no conversation_id, creates a new conversation with LLM-generated title.
        Returns (conversation_id, task_id).
        """
        # 1. Auto-create conversation if standalone
        if conversation_id is None:
            title, description = await self._generate_title(workflow, kwargs)
            conversation_id = self.store.create_conversation(
                title, description)

        # 2. Create TaskPart and insert as assistant message
        task_part = TaskPart(
            task_id=...,
            title=f"{workflow.name}: {kwargs.get('node_id', '')}",
            workflow_name=workflow.name,
            workflow_params=kwargs,
        )
        self.store.add_message(conversation_id, ConversationMessage(
            id=..., role=MessageRole.ASSISTANT,
            parts=[TextPart(text=f"Starting {workflow.name}..."), task_part],
        ))

        # 3. Submit to background with progress callback
        task_id = self.task_manager.submit(
            name=f"workflow:{workflow.name}",
            coro_factory=workflow.run,
            on_subtask_update=lambda st: self._update_task_part(
                conversation_id, task_part, st),
            **kwargs,
        )
        return conversation_id, task_id

    async def _generate_title(self, workflow, params) -> tuple[str, str]:
        """Use LLM to generate conversation title + description from the workflow."""
        llm = self.llm_factory.create(model="gpt-4o-mini")
        # ... prompt LLM to generate title/description
        ...

    def _update_task_part(self, conv_id, task_part, sub_task: SubTask):
        """Update TaskPart's sub_tasks list and push via WebSocket."""
        task_part.sub_tasks.append(sub_task)
        task_part.touched_node_ids.extend(sub_task.touched_node_ids)
        # Push real-time update via WebSocket
        ...
