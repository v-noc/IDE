from __future__ import annotations

from typing import Any

from app.agent.schemas.constants import WIRE_PROTOCOL


def open_frame(doc: str, snapshot: dict[str, Any], *, protocol: int = WIRE_PROTOCOL) -> dict[str, Any]:
    return {
        "kind": "open",
        "doc": doc,
        "protocol": protocol,
        "snapshot": snapshot,
    }


def patch_frame(doc: str, seq: int, ops: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "kind": "patch",
        "doc": doc,
        "seq": seq,
        "ops": ops,
    }


def close_frame(doc: str, status: str, message: str | None = None) -> dict[str, Any]:
    frame: dict[str, Any] = {
        "kind": "close",
        "doc": doc,
        "status": status,
    }
    if message:
        frame["message"] = message
    return frame
