from __future__ import annotations

import asyncio

from app.agent.harness.patcher import ConversationPatcher
from app.agent.schemas.conversation import MessageMetadata
from app.agent.schemas.parts import TextPart


async def run_echo(
    patcher: ConversationPatcher,
    *,
    assistant_index: int,
    user_text: str,
    cancelled: asyncio.Event | None = None,
    chunk_delay_s: float = 0.02,
) -> MessageMetadata:
    """Phase-1 stand-in for the agent loop: stream a deterministic echo reply."""
    reply = f"Echo: {user_text}" if user_text else "Echo: (empty message)"
    part_index = await patcher.add_part(assistant_index, TextPart(text=""))

    # Stream in small chunks so the wire path exercises `append`.
    chunk_size = max(1, len(reply) // 6) if len(reply) > 6 else 1
    for start in range(0, len(reply), chunk_size):
        if cancelled is not None and cancelled.is_set():
            return MessageMetadata(
                model_id="fake:echo",
                stop_reason="cancelled",
            )
        await patcher.append_text(assistant_index, part_index, reply[start : start + chunk_size])
        if chunk_delay_s > 0:
            await asyncio.sleep(chunk_delay_s)

    return MessageMetadata(
        model_id="fake:echo",
        stop_reason="end_turn",
    )
