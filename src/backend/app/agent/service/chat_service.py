import uuid
import asyncio
import logging

from langchain_core.messages import AIMessage, HumanMessage

from app.agent.conversation_store import ConversationStore
from app.agent.llm.gateway import LLMGateway
from app.agent.streaming.manager import StreamManager, StreamHandle
from app.agent.realtime import (
    conversation_message_to_wire,
    emit_conversation_patch,
)
from app.agent.runner.patch_builder import ConversationPatchBuilder
from app.agent.runner.task_manager import TaskManager
from app.agent.chat.completion_params import ChatCompletionParams
from app.core.model.conversation_domain import (
    ConversationMessage,
    TextPart,
)
from app.core.model.conversation_enums import MessageRole

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(
        self,
        task_manager: TaskManager,
        llm_gateway: LLMGateway,
        stream_manager: StreamManager,
    ):
        self._tasks = task_manager
        self._llm = llm_gateway
        self._streams = stream_manager

    async def send_message(
        self,
        conversation_id: str,
        user_message: ConversationMessage,
        *,
        store: ConversationStore,
        completion_params: ChatCompletionParams | None = None,
        client_ref: str | None = None,
    ) -> dict:
        # 1. Persist user message
        user_mid = await store.add_message(
            conversation_id, user_message
        )
        meta = await store.get_conversation_metadata(conversation_id)
        if meta is None:
            raise ValueError(f"Conversation not found: {conversation_id}")

        # 2. Broadcast user message patch
        await self._emit_user_patch(
            conversation_id, user_message, user_mid, meta
        )

        # 3. Open stream + submit background generation
        handle = self._streams.open(conversation_id)
        task_id = self._tasks.submit(
            name="chat:response",
            coro_factory=self._generate,
            store=store,
            conversation_id=conversation_id,
            handle=handle,
            completion_params=completion_params,
            client_ref=client_ref,
        )

        return {
            "conversation_id": conversation_id,
            "message_id": user_mid,
            "task_id": task_id,
            "stream_id": handle.stream_id,
            "client_ref": client_ref,
        }

    async def _generate(
        self,
        *,
        store: ConversationStore,
        conversation_id: str,
        handle: StreamHandle,
        completion_params: ChatCompletionParams | None = None,
        client_ref: str | None = None,
        task_status=None,
    ) -> None:
        resolved = self._llm.resolve(completion_params)

        await self._streams.emit_start(
            handle,
            model=resolved.model,
            provider=resolved.provider_name,
            task_id=getattr(task_status, "id", None),
            client_ref=client_ref,
        )
        try:
            history = await store.list_messages(
                conversation_id, cursor=0, limit=500
            )
            lc_messages = self._to_langchain(history) or [
                HumanMessage(content="")
            ]

            async for delta in resolved.provider.stream(lc_messages):
                if delta:
                    await self._streams.push_chunk(handle, delta)

            full_text = self._streams.finish(handle)
            final_id = await self._persist_assistant(
                store, conversation_id, full_text, resolved.model
            )
            self._streams.set_message_id(handle, final_id)

            await self._emit_assistant_patch(
                store, conversation_id, full_text, final_id
            )
            await self._streams.emit_end(handle, final_id)

        except asyncio.CancelledError:
            await self._streams.emit_error(handle, "cancelled")
            raise
        except Exception as e:
            logger.exception("chat:response failed")
            await self._streams.emit_error(handle, str(e))
            raise
