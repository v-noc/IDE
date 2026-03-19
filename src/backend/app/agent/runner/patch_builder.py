"""RFC 6902 JSON Patch fragments for client conversation state."""

from __future__ import annotations

from typing import Any


class ConversationPatchBuilder:
    """Builds JSON Patch arrays for conversation state mutations."""

    def __init__(self) -> None:
        self._patches: list[dict[str, Any]] = []

    def add(self, path: str, value: Any) -> ConversationPatchBuilder:
        self._patches.append({"op": "add", "path": path, "value": value})
        return self

    def replace(self, path: str, value: Any) -> ConversationPatchBuilder:
        self._patches.append({"op": "replace", "path": path, "value": value})
        return self

    def remove(self, path: str) -> ConversationPatchBuilder:
        self._patches.append({"op": "remove", "path": path})
        return self

    def build(self) -> list[dict[str, Any]]:
        return list(self._patches)

    def task_progress(
        self, task_id: str, progress: float, message: str = ""
    ) -> ConversationPatchBuilder:
        self.replace(f"/tasks/{task_id}/progress", progress)
        if message:
            self.replace(f"/tasks/{task_id}/progress_message", message)
        return self

    def add_message_wire(self, message: dict) -> ConversationPatchBuilder:
        self.add("/messages/-", message)
        return self

    def finalize_assistant_text_part(
        self,
        message_index: int,
        text: str,
        *,
        message_id: str | None = None,
        sequence: int | None = None,
    ) -> ConversationPatchBuilder:
        base = f"/messages/{message_index}"
        self.replace(f"{base}/parts/0/text", text)
        if message_id is not None:
            self.replace(f"{base}/id", message_id)
        if sequence is not None:
            self.replace(f"{base}/sequence", sequence)
        return self

    def message_count(self, n: int) -> ConversationPatchBuilder:
        self.replace("/message_count", n)
        return self
