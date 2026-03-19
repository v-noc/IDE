# agent/runner/executor.py

import asyncio
import logging
import uuid

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.agent.chat.completion_params import ChatCompletionParams
from app.agent.config import settings as agent_settings
from app.agent.conversation_store import ConversationStore
from app.agent.realtime import (
    conversation_message_to_wire,
    emit_conversation_patch,
    emit_to_conversation,
)
from app.agent.runner.patch_builder import ConversationPatchBuilder
from app.agent.runner.stream_buffer import StreamRegistry
from app.agent.runner.task_manager import TaskManager
from app.agent.workflows.base import BaseWorkflow
from app.core.model.conversation_domain import (
    ConversationMessage,
    TaskPart,
    TextPart,
)
from app.core.model.conversation_enums import MessageRole, TaskState as ConversationTaskState
from app.core.model.conversation_nodes import Task

logger = logging.getLogger(__name__)


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
        conversation_store: ConversationStore,
        stream_registry: StreamRegistry | None = None,
    ):
        self.task_manager = task_manager
        self.llm_factory = llm_factory
        self.store = conversation_store
        self.stream_registry = stream_registry or StreamRegistry()
        self._task_part_templates: dict[str, TaskPart] = {}

    @staticmethod
    def _text_from_domain_message(message: ConversationMessage) -> str:
        texts = [p.text for p in message.parts if isinstance(p, TextPart)]
        return "\n".join(texts) if texts else ""

    def _domain_messages_to_lc(self, messages: list[ConversationMessage]):
        out = []
        for m in messages:
            text = self._text_from_domain_message(m)
            if m.role == MessageRole.USER:
                out.append(HumanMessage(content=text))
            elif m.role == MessageRole.ASSISTANT:
                out.append(AIMessage(content=text))
        return out

    def _resolve_llm(self, completion_params: ChatCompletionParams | None):
        params = completion_params or ChatCompletionParams()
        model = params.model or agent_settings.default_model
        provider_name = params.provider or agent_settings.default_provider
        extra = params.provider_create_kwargs()
        mt = extra.get("max_tokens")
        if mt is not None and mt > agent_settings.max_total_tokens:
            extra["max_tokens"] = agent_settings.max_total_tokens
        llm = self.llm_factory.create(
            provider=provider_name,
            model=model,
            **extra,
        )
        return llm, model, provider_name

    async def handle_chat_message(
        self,
        conversation_id: str,
        user_message: ConversationMessage,
        *,
        completion_params: ChatCompletionParams | None = None,
        client_ref: str | None = None,
    ) -> dict:
        """Persist user text, broadcast patch, and stream assistant reply in background."""
        user_mid = await self.store.add_message(conversation_id, user_message)
        meta = await self.store.get_conversation_metadata(conversation_id)
        if meta is None:
            raise ValueError(f"Conversation not found: {conversation_id}")

        user_wire = conversation_message_to_wire(
            user_message.model_copy(
                update={
                    "id": user_mid or user_message.id,
                    "sequence": meta.message_count - 1,
                }
            )
        )
        user_patches = (
            ConversationPatchBuilder()
            .add_message_wire(user_wire)
            .message_count(meta.message_count)
            .build()
        )
        await emit_conversation_patch(conversation_id, user_patches)

        stream_id = str(uuid.uuid4())
        self.stream_registry.create(stream_id, conversation_id)

        task_id = self.task_manager.submit(
            name="chat:response",
            coro_factory=self._generate_response,
            conversation_id=conversation_id,
            stream_id=stream_id,
            completion_params=completion_params,
            client_ref=client_ref,
        )

        return {
            "conversation_id": conversation_id,
            "message_id": user_mid,
            "task_id": task_id,
            "stream_id": stream_id,
            "client_ref": client_ref,
        }

    async def _generate_response(
        self,
        *,
        conversation_id: str,
        stream_id: str,
        task_status: Task | None = None,
        completion_params: ChatCompletionParams | None = None,
        client_ref: str | None = None,
    ) -> None:
        buffer = self.stream_registry.get(stream_id)
        if buffer is None:
            logger.error("Missing stream buffer for stream_id=%s", stream_id)
            return

        provider, resolved_model, resolved_provider = self._resolve_llm(
            completion_params
        )

        payload = {
            "stream_id": stream_id,
            "conversation_id": conversation_id,
            "model": resolved_model,
            "provider": resolved_provider,
        }
        if task_status is not None:
            payload["task_id"] = task_status.id
        if client_ref:
            payload["client_ref"] = client_ref

        await emit_to_conversation(
            conversation_id,
            "stream:start",
            payload,
        )

        try:
            history = await self.store.list_messages(
                conversation_id, cursor=0, limit=500
            )
            lc_messages = self._domain_messages_to_lc(history)
            if not lc_messages:
                lc_messages = [HumanMessage(content="")]

            async for delta in provider.stream(lc_messages):
                if not delta:
                    continue
                seq = buffer.append(delta)
                await emit_to_conversation(
                    conversation_id,
                    "stream:chunk",
                    {
                        "stream_id": stream_id,
                        "seq": seq,
                        "delta": delta,
                    },
                )

            full_text = buffer.finish()
            assistant_id = str(uuid.uuid4())
            assistant_msg = ConversationMessage(
                id=assistant_id,
                role=MessageRole.ASSISTANT,
                parts=[TextPart(text=full_text)],
                model=resolved_model,
            )
            saved_id = await self.store.add_message(
                conversation_id, assistant_msg
            )
            final_id = saved_id or assistant_id
            buffer.set_message_id(final_id)

            meta = await self.store.get_conversation_metadata(conversation_id)
            if meta is None:
                raise RuntimeError("conversation disappeared after save")

            msg_index = meta.message_count - 1
            seq_value = msg_index
            finalize_patches = (
                ConversationPatchBuilder()
                .finalize_assistant_text_part(
                    msg_index,
                    full_text,
                    message_id=final_id,
                    sequence=seq_value,
                )
                .message_count(meta.message_count)
                .build()
            )
            await emit_conversation_patch(conversation_id, finalize_patches)

            await emit_to_conversation(
                conversation_id,
                "stream:end",
                {
                    "stream_id": stream_id,
                    "message_id": final_id,
                    "total_seq": buffer.next_seq,
                },
            )
        except asyncio.CancelledError:
            await emit_to_conversation(
                conversation_id,
                "stream:error",
                {"stream_id": stream_id, "error": "cancelled"},
            )
            raise
        except Exception as e:
            logger.exception("chat:response failed")
            await emit_to_conversation(
                conversation_id,
                "stream:error",
                {"stream_id": stream_id, "error": str(e)},
            )
            raise
        finally:
            self.stream_registry.schedule_remove(stream_id)

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
            conversation_id = await self.store.create_conversation(
                title, description
            )

        async def _on_status(status: Task) -> None:
            await self._update_task_part(
                conversation_id, task_id, status
            )

        # 2. Submit task and attach a timeline message to the conversation
        task_id = self.task_manager.submit(
            name=f"workflow:{workflow.name}",
            coro_factory=workflow.run,
            on_status_update=_on_status,
            **kwargs,
        )

        task_part = TaskPart(
            task_id=task_id,
            title=f"{workflow.name}: {kwargs.get('node_id', '')}",
            workflow_name=workflow.name,
            workflow_params=kwargs,
        )
        await self.store.add_message(
            conversation_id,
            ConversationMessage(
                id=str(uuid.uuid4()),
                role=MessageRole.ASSISTANT,
                parts=[TextPart(text=f"Starting {workflow.name}..."), task_part],
            ),
        )
        self._task_part_templates[task_id] = task_part
        # Push initial state after the message has been written.
        await self._update_task_part(
            conversation_id,
            task_id,
            self.task_manager.get_status(task_id),
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

    async def _update_task_part(
        self,
        conversation_id: str,
        task_id: str,
        task_status: Task | None,
    ) -> None:
        """Update existing TaskPart container for one workflow task."""
        if task_status is None:
            return

        base_part = self._task_part_templates.get(task_id)
        if base_part is None:
            base_part = TaskPart(task_id=task_id, title=task_status.name)

        updated_part = base_part.model_copy(
            update={
                "state": ConversationTaskState(task_status.state.value),
                "progress": task_status.progress,
                "description": task_status.progress_message or "",
                "started_at": task_status.started_at,
                "finished_at": task_status.finished_at,
            }
        )
        await self.store.upsert_task_part(conversation_id, updated_part)
        self._task_part_templates[task_id] = updated_part
