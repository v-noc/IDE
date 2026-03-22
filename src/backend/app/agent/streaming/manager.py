# agent/streaming/manager.py

import uuid
import asyncio
import logging
from dataclasses import dataclass

from app.agent.realtime import emit_to_conversation
from app.agent.runner.stream_buffer import StreamRegistry

logger = logging.getLogger(__name__)


@dataclass
class StreamHandle:
    stream_id: str
    conversation_id: str


class StreamManager:
    def __init__(self, registry: StreamRegistry | None = None):
        self._registry = registry or StreamRegistry()

    def open(self, conversation_id: str) -> StreamHandle:
        stream_id = str(uuid.uuid4())
        self._registry.create(stream_id, conversation_id)
        return StreamHandle(
            stream_id=stream_id,
            conversation_id=conversation_id,
        )

    async def emit_start(
        self,
        handle: StreamHandle,
        *,
        model: str,
        provider: str,
        task_id: str | None = None,
        client_ref: str | None = None,
    ) -> None:
        payload = {
            "stream_id": handle.stream_id,
            "conversation_id": handle.conversation_id,
            "model": model,
            "provider": provider,
        }
        if task_id:
            payload["task_id"] = task_id
        if client_ref:
            payload["client_ref"] = client_ref
        await emit_to_conversation(
            handle.conversation_id, "stream:start", payload
        )

    async def push_chunk(
        self, handle: StreamHandle, delta: str
    ) -> int | None:
        buf = self._registry.get(handle.stream_id)
        if buf is None:
            return None
        seq = buf.append(delta)
        await emit_to_conversation(
            handle.conversation_id,
            "stream:chunk",
            {
                "stream_id": handle.stream_id,
                "seq": seq,
                "delta": delta,
            },
        )
        return seq

    def finish(self, handle: StreamHandle) -> str:
        buf = self._registry.get(handle.stream_id)
        if buf is None:
            return ""
        return buf.finish()

    def set_message_id(
        self, handle: StreamHandle, message_id: str
    ) -> None:
        buf = self._registry.get(handle.stream_id)
        if buf:
            buf.set_message_id(message_id)

    def next_seq(self, handle: StreamHandle) -> int:
        buf = self._registry.get(handle.stream_id)
        return buf.next_seq if buf else 0

    async def emit_end(
        self, handle: StreamHandle, message_id: str
    ) -> None:
        await emit_to_conversation(
            handle.conversation_id,
            "stream:end",
            {
                "stream_id": handle.stream_id,
                "message_id": message_id,
                "total_seq": self.next_seq(handle),
            },
        )
        self._registry.schedule_remove(handle.stream_id)

    async def emit_error(
        self, handle: StreamHandle, error: str
    ) -> None:
        await emit_to_conversation(
            handle.conversation_id,
            "stream:error",
            {"stream_id": handle.stream_id, "error": error},
        )
        self._registry.schedule_remove(handle.stream_id)
