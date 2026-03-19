# agent/runner/executor.py

from agent.runner.task_manager import TaskManager
from agent.graph.builder import build_agent_graph
from agent.workflows.base import BaseWorkflow
from app.agent.models.conversation import ConversationMessage, MessageRole, SubTask, TaskPart, TextPart
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field


class ConversationTitleOutput(BaseModel):
    """Structured output payload for conversation metadata."""

    title: str = Field(
        description="Short conversation title (3-8 words).",
        min_length=3,
        max_length=80,
    )
    description: str = Field(
        description="One sentence summary of the workflow execution goal.",
        min_length=8,
        max_length=220,
    )


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
        workflow_name = getattr(workflow, "name", "workflow")
        safe_workflow_name = workflow_name.replace("_", " ").strip().title()
        fallback_title = f"{safe_workflow_name} Run"
        fallback_description = f"Run `{workflow_name}` with the provided parameters."

        # Keep prompt payload compact and deterministic.
        if not params:
            params_preview = "None"
        else:
            preview_items = []
            for key, value in list(params.items())[:8]:
                value_str = repr(value)
                if len(value_str) > 80:
                    value_str = f"{value_str[:77]}..."
                preview_items.append(f"{key}={value_str}")
            params_preview = ", ".join(preview_items)

        messages = [
            SystemMessage(
                content=(
                    "You generate concise conversation metadata for backend workflow runs. "
                    "Return neutral, technical text without markdown or quotes."
                )
            ),
            HumanMessage(
                content=(
                    f"Workflow name: {workflow_name}\n"
                    f"Workflow description: {getattr(workflow, 'description', '')}\n"
                    f"Parameters: {params_preview}\n\n"
                    "Generate:\n"
                    "1) title: short and specific\n"
                    "2) description: one sentence, action-oriented"
                )
            ),
        ]

        try:
            provider = self.llm_factory.create(model="gpt-4o-mini")
            base_llm = getattr(provider, "_llm", None)
            if base_llm is None:
                return fallback_title, fallback_description

            structured_llm = base_llm.with_structured_output(
                ConversationTitleOutput)
            result = await structured_llm.ainvoke(messages)

            title = result.title.strip().strip("\"'")
            description = result.description.strip().strip("\"'")
            if not title:
                title = fallback_title
            if not description:
                description = fallback_description
            return title, description
        except Exception:
            # Never block workflow scheduling on title generation issues.
            return fallback_title, fallback_description

    def _update_task_part(self, conv_id, task_part, sub_task: SubTask):
        """Update TaskPart's sub_tasks list and push via WebSocket."""
        task_part.sub_tasks.append(sub_task)
        task_part.touched_node_ids.extend(sub_task.touched_node_ids)
        # Push real-time update via WebSocket
        ...
