from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware import AgentMiddleware, ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.types import interrupt
from loguru import logger

from app.agent.schemas.parts import ToolEstimate
from app.agent.tools.base import (
    ToolOutcome,
    get_tool_registry,
    get_tool_services,
    needs_confirmation,
)
from app.config.settings import get_settings


class EstimateConfirmMiddleware(AgentMiddleware):
    """Estimate task tools → interrupt() when over threshold / always."""

    def __init__(self, *, auto_run_limit: int | None = None):
        settings = get_settings()
        self.auto_run_limit = (
            auto_run_limit
            if auto_run_limit is not None
            else settings.AGENT_AUTO_RUN_LIMIT
        )

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[Any]],
    ) -> Any:
        tool_call = request.tool_call
        name = tool_call.get("name") if isinstance(tool_call, dict) else getattr(
            tool_call, "name", None,
        )
        call_id = tool_call.get("id") if isinstance(tool_call, dict) else getattr(
            tool_call, "id", "",
        )
        raw_args = tool_call.get("args") if isinstance(tool_call, dict) else getattr(
            tool_call, "args", {},
        )

        registry = get_tool_registry()
        try:
            spec = registry.get(name)
        except KeyError:
            return await handler(request)

        if spec.kind != "task":
            return await handler(request)

        services = get_tool_services()
        args = spec.input_model.model_validate(raw_args)

        # Notify UI: pending
        if services.on_tool_pending is not None:
            await services.on_tool_pending(
                call_id,
                name,
                args.model_dump(),
            )

        try:
            estimate: ToolEstimate = await spec.handler.estimate(args, services)
        except Exception as exc:
            logger.exception("tool estimate failed: {}", exc)
            return ToolMessage(
                content=f"estimate failed: {exc}",
                tool_call_id=call_id,
                name=name,
            )

        if estimate.over_cap:
            msg = (
                f"Refused: {estimate.label} exceeds the visit cap. "
                "Try a smaller depth."
            )
            if services.on_tool_error is not None:
                await services.on_tool_error(call_id, msg)
            return ToolMessage(
                content=msg,
                tool_call_id=call_id,
                name=name,
            )

        if needs_confirmation(spec, estimate, self.auto_run_limit):
            logger.info(
                "tool {} confirm (llm_calls={}, limit={})",
                name,
                estimate.llm_calls,
                self.auto_run_limit,
            )
            if services.on_awaiting_confirmation is not None:
                await services.on_awaiting_confirmation(
                    call_id,
                    name,
                    args.model_dump(),
                    estimate,
                )
            decision = interrupt(
                {
                    "tool_call_id": call_id,
                    "tool": name,
                    "estimate": estimate.model_dump(),
                    "knobs": estimate.knobs,
                    "args": args.model_dump(),
                },
            )
            # Resume payload: {decision: approve|cancel, overrides?: dict}
            if not isinstance(decision, dict):
                decision = {"decision": "cancel"}
            if decision.get("decision") == "cancel":
                if services.on_tool_error is not None:
                    await services.on_tool_error(call_id, "declined by user")
                return ToolMessage(
                    content="declined by user",
                    tool_call_id=call_id,
                    name=name,
                )
            overrides = decision.get("overrides") or {}
            if overrides:
                merged = {**args.model_dump(), **overrides}
                args = spec.input_model.model_validate(merged)
                # Rewrite tool call args so the StructuredTool sees overrides
                if isinstance(tool_call, dict):
                    tool_call = {**tool_call, "args": args.model_dump()}
                    request = request.override(tool_call=tool_call)  # type: ignore[attr-defined]
                else:
                    # mutate if possible
                    try:
                        tool_call["args"] = args.model_dump()  # type: ignore[index]
                    except Exception:
                        pass

        else:
            logger.info(
                "tool {} auto_run (llm_calls={}, limit={})",
                name,
                estimate.llm_calls,
                self.auto_run_limit,
            )

        if services.on_tool_running is not None:
            await services.on_tool_running(call_id, args.model_dump())

        started = time.monotonic()
        try:
            result = await handler(request)
        except Exception as exc:
            if services.on_tool_error is not None:
                await services.on_tool_error(call_id, str(exc))
            raise
        duration_ms = int((time.monotonic() - started) * 1000)

        if isinstance(result, ToolMessage):
            if result.status == "error":
                if services.on_tool_error is not None:
                    await services.on_tool_error(call_id, str(result.content))
            elif services.on_tool_completed is not None:
                outcome = (
                    result.artifact
                    if isinstance(result.artifact, ToolOutcome)
                    else None
                )
                await services.on_tool_completed(
                    call_id,
                    input_args=args.model_dump(),
                    result=outcome.result if outcome else {"content": str(result.content)},
                    artifact=outcome.artifact if outcome else None,
                    degraded=outcome.degraded if outcome else False,
                    duration_ms=duration_ms,
                )
        return result
