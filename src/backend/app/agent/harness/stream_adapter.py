from __future__ import annotations

import time
from typing import Any

from app.agent.harness.patcher import ConversationPatcher
from app.agent.harness.usage import estimate_cost_usd, extract_usage, merge_usage
from app.agent.schemas.conversation import MessageMetadata, TokenUsage
from app.agent.schemas.parts import ReasoningPart, TextPart


def _content_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(str(block.get("text") or ""))
                elif block.get("type") == "thinking":
                    parts.append(str(block.get("thinking") or ""))
            elif hasattr(block, "text"):
                parts.append(str(getattr(block, "text") or ""))
        return "".join(parts)
    return str(content)


def _reasoning_delta(message: Any) -> str:
    kwargs = getattr(message, "additional_kwargs", None) or {}
    if isinstance(kwargs, dict):
        for key in ("reasoning_content", "reasoning", "thinking"):
            val = kwargs.get(key)
            if isinstance(val, str) and val:
                return val
    content = getattr(message, "content", None)
    if isinstance(content, list):
        chunks: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") in (
                "thinking",
                "reasoning",
            ):
                chunks.append(
                    str(block.get("thinking") or block.get("text") or ""),
                )
        return "".join(chunks)
    return ""


class StreamAdapter:
    """LangGraph/LangChain stream events → conversation patch helpers."""

    def __init__(
        self,
        patcher: ConversationPatcher,
        *,
        assistant_index: int,
        model_id: str,
        prompt_version: str | None = None,
        effort: str | None = None,
    ):
        self.patcher = patcher
        self.assistant_index = assistant_index
        self.model_id = model_id
        self.prompt_version = prompt_version
        self.effort = effort
        self._text_part: int | None = None
        self._reasoning_part: int | None = None
        self._reasoning_started: float | None = None
        self._stop_reason = "end_turn"
        self._usage: TokenUsage | None = None
        self._started_at = time.monotonic()
        self._error: str | None = None

    async def on_message_chunk(self, message: Any) -> None:
        usage = extract_usage(message)
        if usage is not None:
            self._usage = merge_usage(self._usage, usage)

        reasoning = _reasoning_delta(message)
        if reasoning:
            if self._reasoning_part is None:
                self._reasoning_started = time.monotonic()
                self._reasoning_part = await self.patcher.add_part(
                    self.assistant_index,
                    ReasoningPart(origin="native", text=""),
                )
            await self.patcher.append_text(
                self.assistant_index,
                self._reasoning_part,
                reasoning,
            )

        text = _content_text(getattr(message, "content", None))
        if isinstance(getattr(message, "content", None), list):
            text = "".join(
                str(b.get("text") or "")
                if isinstance(b, dict) and b.get("type") == "text"
                else (b if isinstance(b, str) else "")
                for b in message.content
            )
        if not text:
            return

        if self._reasoning_part is not None and self._reasoning_started is not None:
            duration_ms = int((time.monotonic() - self._reasoning_started) * 1000)
            conv = self.patcher.conversation
            part = conv.messages[self.assistant_index].parts[self._reasoning_part]
            if isinstance(part, ReasoningPart):
                settled = part.model_copy(update={"duration_ms": duration_ms})
                await self.patcher.set_part(
                    self.assistant_index,
                    self._reasoning_part,
                    settled,
                    persist=True,
                )
            self._reasoning_started = None

        if self._text_part is None:
            self._text_part = await self.patcher.add_part(
                self.assistant_index,
                TextPart(text=""),
            )
        await self.patcher.append_text(
            self.assistant_index,
            self._text_part,
            text,
        )

    def mark_max_steps(self) -> None:
        self._stop_reason = "max_steps"

    def mark_cancelled(self) -> None:
        self._stop_reason = "cancelled"

    def mark_error(self, message: str | None = None) -> None:
        self._stop_reason = "error"
        if message:
            self._error = message

    def metadata(self) -> MessageMetadata:
        duration_ms = int((time.monotonic() - self._started_at) * 1000)
        return MessageMetadata(
            model_id=self.model_id,
            prompt_version=self.prompt_version,
            effort=self.effort,  # type: ignore[arg-type]
            usage=self._usage,
            cost_usd=estimate_cost_usd(self.model_id, self._usage),
            duration_ms=duration_ms,
            stop_reason=self._stop_reason,  # type: ignore[arg-type]
            error=self._error,
        )
