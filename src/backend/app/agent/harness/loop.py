from __future__ import annotations

import asyncio
from typing import Any

from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import GraphInterrupt
from langgraph.types import Command
from loguru import logger

from app.agent.harness.confirm import EstimateConfirmMiddleware
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
from app.agent.harness.tool_tracker import ToolPartTracker
from app.agent.prompts.registry import get_prompt_registry
from app.agent.schemas.conversation import Conversation, EffortLevel, MessageMetadata
from app.agent.tools import walkthrough_tool as _wt  # noqa: F401 — register
from app.agent.tools.base import (
    ToolServices,
    get_tool_registry,
    langchain_tools,
    reset_tool_services,
    set_tool_services,
)
from app.config.settings import get_settings
from app.core.services.code_element_service import CodeElementService
from app.db.context import ProjectUoW

_checkpointer = MemorySaver()


def _build_agent(chat, project, repos, node_refs, attached, tools_blurb: str):
    project_mw = ProjectContextMiddleware(project, tools_blurb=tools_blurb)
    limits = build_limits_middleware(get_settings().AGENT_MAX_STEPS)
    enrichment = NodeEnrichmentMiddleware(repos, node_refs, attached)
    confirm = EstimateConfirmMiddleware()
    return create_agent(
        model=chat,
        tools=langchain_tools(),
        middleware=[project_mw, enrichment, confirm, limits],
        checkpointer=_checkpointer,
    )


async def _stream_agent(
    agent,
    *,
    input_payload: dict[str, Any] | Command,
    config: dict[str, Any],
    adapter: StreamAdapter,
    cancelled: asyncio.Event | None,
) -> bool:
    """Returns True if the run suspended on interrupt (awaiting confirmation)."""
    try:
        async for item in agent.astream(
            input_payload,
            config=config,
            stream_mode="messages",
        ):
            if cancelled is not None and cancelled.is_set():
                adapter.mark_cancelled()
                break
            message = item[0] if isinstance(item, tuple) else item
            await adapter.on_message_chunk(message)
        return False
    except GraphInterrupt:
        return True
    except Exception as exc:
        # Some LangGraph versions wrap interrupt differently
        if "Interrupt" in type(exc).__name__ or "interrupt" in str(exc).lower():
            return True
        raise


async def run_agent_turn(
    patcher: ConversationPatcher,
    *,
    conversation: Conversation,
    assistant_index: int,
    uow: ProjectUoW,
    effort: EffortLevel | None = None,
    cancelled: asyncio.Event | None = None,
    emit: Any = None,
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

    tracker = ToolPartTracker(patcher, assistant_index)

    async def on_pending(call_id, name, args):
        await tracker.pending(call_id, name, args)

    async def on_awaiting(call_id, name, args, estimate):
        await tracker.awaiting(call_id, name, args, estimate)

    async def on_running(call_id, input_args=None):
        await tracker.running(call_id, input_args)

    async def on_completed(
        call_id, *, input_args, result, artifact=None, degraded=False, duration_ms=0,
    ):
        await tracker.completed(
            call_id,
            input_args=input_args,
            result=result,
            artifact=artifact,
            degraded=degraded,
            duration_ms=duration_ms,
        )

    async def on_error(call_id, message):
        await tracker.error(call_id, message)

    services = ToolServices(
        uow=uow,
        patcher=patcher,
        conversation_id=conversation.id,
        emit=emit,
        on_tool_pending=on_pending,
        on_awaiting_confirmation=on_awaiting,
        on_tool_running=on_running,
        on_tool_completed=on_completed,
        on_tool_error=on_error,
    )
    token = set_tool_services(services)

    tools_blurb = get_tool_registry().tools_blurb()
    agent = _build_agent(
        chat, uow.project, repos, node_refs, attached, tools_blurb,
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
        interrupted = await _stream_agent(
            agent,
            input_payload={"messages": messages},
            config=config,
            adapter=adapter,
            cancelled=cancelled,
        )
        if interrupted:
            # Leave stream open; status already awaiting_confirmation
            meta = adapter.metadata()
            meta.stop_reason = None
            return meta
    except Exception as exc:
        logger.exception("agent astream failed: {}", exc)
        adapter.mark_error(str(exc))
        meta = adapter.metadata()
        meta.error = str(exc)
        return meta
    finally:
        reset_tool_services(token)

    return adapter.metadata()


async def resume_agent_turn(
    patcher: ConversationPatcher,
    *,
    conversation: Conversation,
    assistant_index: int,
    uow: ProjectUoW,
    decision: dict[str, Any],
    effort: EffortLevel | None = None,
    cancelled: asyncio.Event | None = None,
    emit: Any = None,
) -> MessageMetadata:
    """Resume after POST /decision with Command(resume=...)."""
    settings = get_settings()
    chat, model_id = build_agent_model(effort=effort, settings=settings)
    if chat is None:
        raise RuntimeError("resume_agent_turn called with fake provider")
    if uow.project is None:
        raise RuntimeError("Project context required")

    repos = uow.get_project_repos()
    node_refs = latest_node_refs(conversation)
    attached: dict[str, str] = {}
    tracker = ToolPartTracker(patcher, assistant_index)

    async def on_pending(call_id, name, args):
        await tracker.pending(call_id, name, args)

    async def on_awaiting(call_id, name, args, estimate):
        await tracker.awaiting(call_id, name, args, estimate)

    async def on_running(call_id, input_args=None):
        await tracker.running(call_id, input_args)
        await patcher.set_status("running")

    async def on_completed(
        call_id, *, input_args, result, artifact=None, degraded=False, duration_ms=0,
    ):
        await tracker.completed(
            call_id,
            input_args=input_args,
            result=result,
            artifact=artifact,
            degraded=degraded,
            duration_ms=duration_ms,
        )

    async def on_error(call_id, message):
        await tracker.error(call_id, message)

    services = ToolServices(
        uow=uow,
        patcher=patcher,
        conversation_id=conversation.id,
        emit=emit,
        on_tool_pending=on_pending,
        on_awaiting_confirmation=on_awaiting,
        on_tool_running=on_running,
        on_tool_completed=on_completed,
        on_tool_error=on_error,
    )
    token = set_tool_services(services)

    agent = _build_agent(
        chat,
        uow.project,
        repos,
        node_refs,
        attached,
        get_tool_registry().tools_blurb(),
    )
    adapter = StreamAdapter(
        patcher,
        assistant_index=assistant_index,
        model_id=model_id,
        prompt_version=get_prompt_registry().version("agent.system"),
        effort=effort or settings.AGENT_REASONING_EFFORT,
    )
    config: dict[str, Any] = {
        "configurable": {"thread_id": conversation.id},
        "recursion_limit": max(settings.AGENT_MAX_STEPS * 2, 25),
    }

    try:
        interrupted = await _stream_agent(
            agent,
            input_payload=Command(resume=decision),
            config=config,
            adapter=adapter,
            cancelled=cancelled,
        )
        if interrupted:
            meta = adapter.metadata()
            meta.stop_reason = None
            return meta
    except Exception as exc:
        logger.exception("agent resume failed: {}", exc)
        adapter.mark_error(str(exc))
        meta = adapter.metadata()
        meta.error = str(exc)
        return meta
    finally:
        reset_tool_services(token)

    return adapter.metadata()
