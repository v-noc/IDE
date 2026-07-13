from __future__ import annotations

import asyncio
from typing import Any

from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from loguru import logger

from app.agent.harness.history import build_history, latest_node_refs
from app.agent.harness.middleware import (
    NodeEnrichmentMiddleware,
    ProjectContextMiddleware,
    build_attached_blocks,
    build_limits_middleware,
)
from app.agent.harness.model import build_agent_model
from app.agent.harness.patcher import ConversationPatcher
from app.agent.harness.stream_adapter import StreamAdapter
from app.agent.prompts.registry import get_prompt_registry
from app.agent.schemas.conversation import Conversation, EffortLevel, MessageMetadata
from app.config.settings import get_settings
from app.core.services.code_element_service import CodeElementService
from app.db.context import ProjectUoW

_checkpointer = MemorySaver()


async def run_agent_turn(
    patcher: ConversationPatcher,
    *,
    conversation: Conversation,
    assistant_index: int,
    uow: ProjectUoW,
    effort: EffortLevel | None = None,
    cancelled: asyncio.Event | None = None,
) -> MessageMetadata:
    settings = get_settings()
    chat, model_id = build_agent_model(effort=effort, settings=settings)
    if chat is None:
        raise RuntimeError("run_agent_turn called with fake provider")

    if uow.project is None:
        raise RuntimeError("Project context required for agent turn")

    repos = uow.get_project_repos()
    code_service = CodeElementService(uow)

    async def code_loader(node_id: str) -> str | None:
        try:
            result = await code_service.get_code(node_id)
        except Exception:
            return None
        if not result:
            return None
        return result.get("code") or result.get("content")

    node_refs = latest_node_refs(conversation)
    attached = await build_attached_blocks(
        repos,
        node_refs,
        code_loader=code_loader,
    )

    project_mw = ProjectContextMiddleware(uow.project)
    limits = build_limits_middleware(settings.AGENT_MAX_STEPS)
    enrichment = NodeEnrichmentMiddleware(repos, node_refs, attached)

    agent = create_agent(
        model=chat,
        tools=[],
        middleware=[project_mw, enrichment, limits],
        checkpointer=_checkpointer,
    )

    messages = build_history(conversation, attached_blocks=attached)
    applied_effort = effort or settings.AGENT_REASONING_EFFORT
    adapter = StreamAdapter(
        patcher,
        assistant_index=assistant_index,
        model_id=model_id,
        prompt_version=get_prompt_registry().version("agent.system"),
        effort=applied_effort if applied_effort in (
            "off", "low", "medium", "high",
        ) else "medium",
    )

    config: dict[str, Any] = {
        "configurable": {"thread_id": conversation.id},
        "recursion_limit": max(settings.AGENT_MAX_STEPS * 2, 25),
    }

    try:
        async for item in agent.astream(
            {"messages": messages},
            config=config,
            stream_mode="messages",
        ):
            if cancelled is not None and cancelled.is_set():
                adapter.mark_cancelled()
                break

            # stream_mode=messages yields (message, metadata) tuples
            message = item[0] if isinstance(item, tuple) else item
            await adapter.on_message_chunk(message)
    except Exception as exc:
        logger.exception("agent astream failed: {}", exc)
        adapter.mark_error()
        meta = adapter.metadata()
        meta.error = str(exc)
        return meta

    return adapter.metadata()
