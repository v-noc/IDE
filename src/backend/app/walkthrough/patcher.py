from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import jsonpatch

from app.walkthrough.schemas import BlockStep, NodeSteps, VisitMode, WalkthroughSession


EmitFn = Callable[[dict[str, Any]], Awaitable[None]]


class Patcher:
    def __init__(self, session: WalkthroughSession, emit: EmitFn):
        self.mirror = session.model_copy(deep=True)
        self.emit = emit
        self.seq = -1
        self.log: list[dict[str, Any]] = []

    async def hello_frame(self) -> dict[str, Any]:
        frame = {"kind": "hello", "protocol": 1, "session": self.mirror.model_dump()}
        self.log.append(frame)
        return frame

    async def open_node_steps(
        self,
        visit_order: int,
        node_id: str,
        mode: VisitMode,
    ) -> None:
        skeleton = NodeSteps(node_id=node_id, order=visit_order, mode=mode)
        await self._frame(
            [{"op": "add", "path": "/node_steps/-", "value": skeleton.model_dump()}],
        )

    async def set_intro(self, visit_order: int, text: str, degraded: bool) -> None:
        index = self._index_for_order(visit_order)
        await self._frame(
            [
                {"op": "replace", "path": f"/node_steps/{index}/intro_text", "value": text},
                {
                    "op": "replace",
                    "path": f"/node_steps/{index}/degraded",
                    "value": degraded,
                },
            ],
        )

    async def add_block(self, visit_order: int, block: BlockStep) -> None:
        index = self._index_for_order(visit_order)
        await self._frame(
            [
                {
                    "op": "add",
                    "path": f"/node_steps/{index}/blocks/-",
                    "value": block.model_dump(),
                },
            ],
        )

    async def set_block_text(
        self,
        visit_order: int,
        block_index: int,
        text: str,
        degraded: bool,
    ) -> None:
        node_index = self._index_for_order(visit_order)
        await self._frame(
            [
                {
                    "op": "replace",
                    "path": f"/node_steps/{node_index}/blocks/{block_index}/text",
                    "value": text,
                },
                {
                    "op": "replace",
                    "path": f"/node_steps/{node_index}/blocks/{block_index}/degraded",
                    "value": degraded,
                },
            ],
        )

    async def set_status(self, status: str) -> None:
        await self._frame([{"op": "replace", "path": "/status", "value": status}])

    async def append_error(self, message: str) -> None:
        await self._frame(
            [{"op": "add", "path": "/error_log/-", "value": message}],
        )

    async def end_frame(self, status: str, message: str | None = None) -> dict[str, Any]:
        frame: dict[str, Any] = {"kind": "end", "status": status}
        if message:
            frame["message"] = message
        self.log.append(frame)
        return frame

    def _index_for_order(self, visit_order: int) -> int:
        for index, step in enumerate(self.mirror.node_steps):
            if step.order == visit_order:
                return index
        raise KeyError(f"node_steps missing order {visit_order}")

    async def _frame(self, ops: list[dict[str, Any]]) -> None:
        self.seq += 1
        patch = jsonpatch.JsonPatch(ops)
        data = self.mirror.model_dump()
        data = patch.apply(data)
        self.mirror = WalkthroughSession.model_validate(data)

        frame = {"kind": "patch", "seq": self.seq, "ops": ops}
        self.log.append(frame)
        await self.emit(frame)

    async def emit_with_delay(self, frame: dict[str, Any], delay_ms: int = 0) -> None:
        if delay_ms > 0:
            await asyncio.sleep(delay_ms / 1000)
        await self.emit(frame)
