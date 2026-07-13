from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.agent.harness.patcher import ConversationPatcher
from app.agent.schemas.parts import (
    ToolAwaitingConfirmation,
    ToolCompleted,
    ToolError,
    ToolEstimate,
    ToolPart,
    ToolPending,
    ToolRunning,
)


class ToolPartTracker:
    """Keeps tool_call_id → part index for live state patches."""

    def __init__(self, patcher: ConversationPatcher, assistant_index: int):
        self.patcher = patcher
        self.assistant_index = assistant_index
        self._parts: dict[str, int] = {}

    async def pending(self, tool_call_id: str, tool: str, input_args: dict) -> None:
        part = ToolPart(
            tool_call_id=tool_call_id,
            tool=tool,
            state=ToolPending(input=input_args),
        )
        index = await self.patcher.add_part(self.assistant_index, part)
        self._parts[tool_call_id] = index

    async def awaiting(
        self,
        tool_call_id: str,
        tool: str,
        input_args: dict,
        estimate: ToolEstimate,
    ) -> None:
        index = self._parts.get(tool_call_id)
        state = ToolAwaitingConfirmation(
            input=input_args,
            estimate=estimate,
            knobs=estimate.knobs,
        )
        if index is None:
            part = ToolPart(tool_call_id=tool_call_id, tool=tool, state=state)
            index = await self.patcher.add_part(self.assistant_index, part)
            self._parts[tool_call_id] = index
        else:
            await self.patcher.set_tool_state(
                self.assistant_index, index, state,
            )
        await self.patcher.set_status("awaiting_confirmation")

    async def running(self, tool_call_id: str, input_args: dict | None = None) -> None:
        index = self._parts.get(tool_call_id)
        if index is None:
            return
        args = input_args or {}
        await self.patcher.set_tool_state(
            self.assistant_index,
            index,
            ToolRunning(
                input=args,
                started_at=datetime.now(timezone.utc),
            ),
        )
        await self.patcher.set_status("running")

    async def completed(
        self,
        tool_call_id: str,
        *,
        input_args: dict,
        result: dict[str, Any],
        artifact: Any = None,
        degraded: bool = False,
        duration_ms: int = 0,
    ) -> None:
        index = self._parts.get(tool_call_id)
        if index is None:
            return
        await self.patcher.set_tool_state(
            self.assistant_index,
            index,
            ToolCompleted(
                input=input_args,
                result=result,
                artifact=artifact,
                degraded=degraded,
                duration_ms=duration_ms,
            ),
        )

    async def error(
        self,
        tool_call_id: str,
        message: str,
        *,
        input_args: dict | None = None,
        duration_ms: int = 0,
    ) -> None:
        index = self._parts.get(tool_call_id)
        if index is None:
            return
        await self.patcher.set_tool_state(
            self.assistant_index,
            index,
            ToolError(
                input=input_args or {},
                error=message,
                duration_ms=duration_ms,
            ),
        )
