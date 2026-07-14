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

    def _index_for(self, tool_call_id: str) -> int | None:
        index = self._parts.get(tool_call_id)
        if index is not None:
            return index
        found = self.patcher.find_tool_part(self.assistant_index, tool_call_id)
        if found is None:
            return None
        self._parts[tool_call_id] = found[0]
        return found[0]

    def _existing_input(self, index: int) -> dict[str, Any]:
        part = self.patcher.conversation.messages[self.assistant_index].parts[index]
        if isinstance(part, ToolPart):
            return dict(part.state.input)
        return {}

    async def pending(self, tool_call_id: str, tool: str, input_args: dict) -> None:
        index = self._index_for(tool_call_id)
        state = ToolPending(input=input_args)
        if index is not None:
            await self.patcher.set_tool_state(self.assistant_index, index, state)
            return
        part = ToolPart(
            tool_call_id=tool_call_id,
            tool=tool,
            state=state,
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
        index = self._index_for(tool_call_id)
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
        index = self._index_for(tool_call_id)
        if index is None:
            return
        args = input_args if input_args is not None else self._existing_input(index)
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
        index = self._index_for(tool_call_id)
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
        index = self._index_for(tool_call_id)
        if index is None:
            return
        args = input_args if input_args is not None else self._existing_input(index)
        await self.patcher.set_tool_state(
            self.assistant_index,
            index,
            ToolError(
                input=args,
                error=message,
                duration_ms=duration_ms,
            ),
        )
