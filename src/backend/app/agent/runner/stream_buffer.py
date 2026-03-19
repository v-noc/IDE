"""In-memory LLM stream chunks with replay for WebSocket resume."""

from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)


class StreamBuffer:
    """Accumulates LLM token chunks with sequence numbers."""

    def __init__(self, stream_id: str, conversation_id: str):
        self.stream_id = stream_id
        self.conversation_id = conversation_id
        self._chunks: list[str] = []
        self._finished = False
        self._final_text: str | None = None
        self._message_id: str | None = None

    @property
    def next_seq(self) -> int:
        return len(self._chunks)

    def append(self, delta: str) -> int:
        seq = self.next_seq
        self._chunks.append(delta)
        return seq

    def get_chunks_since(self, from_seq: int) -> list[tuple[int, str]]:
        start = max(0, int(from_seq))
        return [(i, self._chunks[i]) for i in range(start, len(self._chunks))]

    def finish(self) -> str:
        self._finished = True
        self._final_text = "".join(self._chunks)
        return self._final_text

    def set_message_id(self, message_id: str) -> None:
        self._message_id = message_id

    @property
    def message_id(self) -> str | None:
        return self._message_id

    @property
    def is_finished(self) -> bool:
        return self._finished


class StreamRegistry:
    """Tracks active streams; keeps finished buffers briefly for replay."""

    def __init__(self, replay_ttl_s: float = 60.0):
        self._active: dict[str, StreamBuffer] = {}
        self.replay_ttl_s = replay_ttl_s

    def create(self, stream_id: str, conversation_id: str) -> StreamBuffer:
        buf = StreamBuffer(stream_id, conversation_id)
        self._active[stream_id] = buf
        return buf

    def get(self, stream_id: str) -> StreamBuffer | None:
        return self._active.get(stream_id)

    def remove(self, stream_id: str) -> None:
        self._active.pop(stream_id, None)

    def schedule_remove(self, stream_id: str) -> None:
        ttl = self.replay_ttl_s

        async def _delayed() -> None:
            try:
                await asyncio.sleep(ttl)
            except asyncio.CancelledError:
                return
            self.remove(stream_id)

        try:
            asyncio.create_task(_delayed())
        except RuntimeError:
            logger.warning("Could not schedule stream buffer cleanup (no loop)")

