"""Socket.IO helpers for conversation rooms and patch envelopes."""

from __future__ import annotations

import logging
from typing import Any

from app.core.socket.manager import get_socket_manager

logger = logging.getLogger(__name__)


def conversation_room(conversation_id: str) -> str:
    return f"conv:{conversation_id}"


async def emit_to_conversation(
    conversation_id: str,
    event: str,
    data: dict[str, Any],
) -> None:
    mgr = get_socket_manager()
    room = conversation_room(conversation_id)
    try:
        await mgr.server.emit(event, data, room=room)
    except Exception as e:
        logger.error("emit_to_conversation failed: %s", e)


async def emit_conversation_patch(
    conversation_id: str,
    patches: list[dict[str, Any]],
) -> None:
    await emit_to_conversation(
        conversation_id,
        "conversation:patch",
        {"conversation_id": conversation_id, "patches": patches},
    )
