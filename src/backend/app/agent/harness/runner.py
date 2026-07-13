from __future__ import annotations

import asyncio
from typing import Any

from app.agent.harness.fake_runner import run_fake_enriched
from app.agent.harness.loop import run_agent_turn
from app.agent.harness.patcher import ConversationPatcher
from app.agent.llm.providers import resolve_agent_llm
from app.agent.schemas.conversation import Conversation, EffortLevel, MessageMetadata
from app.config.settings import get_settings
from app.db.context import ProjectUoW


async def run_turn(
    patcher: ConversationPatcher,
    *,
    conversation: Conversation,
    assistant_index: int,
    uow: ProjectUoW,
    effort: EffortLevel | None = None,
    cancelled: asyncio.Event | None = None,
    emit: Any = None,
) -> MessageMetadata:
    """Dispatch to fake enriched runner or real create_agent loop."""
    settings = get_settings()
    resolved = resolve_agent_llm(settings=settings)
    if resolved.spec.name == "fake":
        return await run_fake_enriched(
            patcher,
            conversation=conversation,
            assistant_index=assistant_index,
            uow=uow,
            effort=effort,
            cancelled=cancelled,
        )
    return await run_agent_turn(
        patcher,
        conversation=conversation,
        assistant_index=assistant_index,
        uow=uow,
        effort=effort,
        cancelled=cancelled,
        emit=emit,
    )
