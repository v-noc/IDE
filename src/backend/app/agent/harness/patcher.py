from __future__ import annotations

from collections.abc import Awaitable, Callable
from copy import deepcopy
from typing import Any

import jsonpatch
from pydantic import BaseModel

from app.agent.harness.frames import close_frame, open_frame, patch_frame
from app.agent.schemas.conversation import (
    Conversation,
    ConversationStatus,
    Message,
    MessageMetadata,
)
from app.agent.schemas.parts import Part, ToolPart, ToolState


EmitFn = Callable[[dict[str, Any]], Awaitable[None]]
PersistFn = Callable[[Conversation], Awaitable[None]]


def _get_path(data: Any, path: str) -> Any:
    """Resolve a JSON-Pointer path against a nested dict/list structure."""
    if not path or path == "/":
        return data
    current = data
    for token in path.lstrip("/").split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(token)]
        else:
            current = current[token]
    return current


def _set_path(data: Any, path: str, value: Any) -> None:
    tokens = path.lstrip("/").split("/")
    current = data
    for token in tokens[:-1]:
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(token)]
        else:
            current = current[token]
    last = tokens[-1].replace("~1", "/").replace("~0", "~")
    if isinstance(current, list):
        current[int(last)] = value
    else:
        current[last] = value


def apply_ops(data: dict[str, Any], ops: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply ops with `append` pre-pass, then standard JSON-Patch."""
    result = deepcopy(data)
    standard: list[dict[str, Any]] = []
    for op in ops:
        if op.get("op") == "append":
            path = op["path"]
            existing = _get_path(result, path)
            if not isinstance(existing, str):
                raise TypeError(f"append target at {path} is not a string")
            _set_path(result, path, existing + str(op["value"]))
        else:
            standard.append(op)
    if standard:
        result = jsonpatch.JsonPatch(standard).apply(result)
    return result


class DocMirror:
    def __init__(self, doc: str, snapshot: dict[str, Any] | BaseModel):
        self.doc = doc
        if isinstance(snapshot, BaseModel):
            self.data = snapshot.model_dump(mode="json")
        else:
            self.data = deepcopy(snapshot)
        self.seq = -1


class ConversationPatcher:
    """Multi-doc patcher focused on the conversation document helpers."""

    def __init__(
        self,
        conversation: Conversation,
        emit: EmitFn,
        *,
        on_persist: PersistFn | None = None,
    ):
        self.emit = emit
        self.on_persist = on_persist
        self.doc_id = conversation.id
        self._docs: dict[str, DocMirror] = {
            self.doc_id: DocMirror(self.doc_id, conversation),
        }
        self.log: list[dict[str, Any]] = []

    @property
    def conversation(self) -> Conversation:
        return Conversation.model_validate(self._docs[self.doc_id].data)

    def mirror_for(self, doc: str) -> DocMirror:
        return self._docs[doc]

    async def open_doc(self, doc: str, snapshot: dict[str, Any] | BaseModel) -> None:
        mirror = DocMirror(doc, snapshot)
        self._docs[doc] = mirror
        frame = open_frame(doc, mirror.data)
        self.log.append(frame)
        await self.emit(frame)

    async def close_doc(
        self,
        doc: str,
        status: str,
        message: str | None = None,
    ) -> None:
        frame = close_frame(doc, status, message)
        self.log.append(frame)
        await self.emit(frame)

    async def open_conversation(self) -> None:
        await self.open_doc(self.doc_id, self._docs[self.doc_id].data)

    async def add_message(self, message: Message) -> int:
        await self._patch(
            self.doc_id,
            [
                {
                    "op": "add",
                    "path": "/messages/-",
                    "value": message.model_dump(mode="json"),
                },
            ],
        )
        return len(self.conversation.messages) - 1

    async def add_part(self, message_index: int, part: Part) -> int:
        await self._patch(
            self.doc_id,
            [
                {
                    "op": "add",
                    "path": f"/messages/{message_index}/parts/-",
                    "value": part.model_dump(mode="json"),
                },
            ],
        )
        return len(self.conversation.messages[message_index].parts) - 1

    async def append_text(self, message_index: int, part_index: int, delta: str) -> None:
        await self._patch(
            self.doc_id,
            [
                {
                    "op": "append",
                    "path": f"/messages/{message_index}/parts/{part_index}/text",
                    "value": delta,
                },
            ],
        )

    async def set_tool_state(
        self,
        message_index: int,
        part_index: int,
        state: ToolState,
    ) -> None:
        await self._patch(
            self.doc_id,
            [
                {
                    "op": "replace",
                    "path": f"/messages/{message_index}/parts/{part_index}/state",
                    "value": state.model_dump(mode="json"),
                },
            ],
            persist=True,
        )

    async def set_status(self, status: ConversationStatus) -> None:
        await self._patch(
            self.doc_id,
            [{"op": "replace", "path": "/status", "value": status}],
            persist=True,
        )

    async def finalize_message(
        self,
        message_index: int,
        metadata: MessageMetadata,
    ) -> None:
        await self._patch(
            self.doc_id,
            [
                {
                    "op": "replace",
                    "path": f"/messages/{message_index}/metadata",
                    "value": metadata.model_dump(mode="json"),
                },
            ],
            persist=True,
        )

    async def _patch(
        self,
        doc: str,
        ops: list[dict[str, Any]],
        *,
        persist: bool = False,
    ) -> None:
        mirror = self._docs[doc]
        mirror.seq += 1
        mirror.data = apply_ops(mirror.data, ops)
        frame = patch_frame(doc, mirror.seq, ops)
        self.log.append(frame)
        await self.emit(frame)
        if persist and doc == self.doc_id and self.on_persist is not None:
            await self.on_persist(self.conversation)

    def find_tool_part(
        self,
        message_index: int,
        tool_call_id: str,
    ) -> tuple[int, ToolPart] | None:
        message = self.conversation.messages[message_index]
        for index, part in enumerate(message.parts):
            if isinstance(part, ToolPart) and part.tool_call_id == tool_call_id:
                return index, part
        return None
