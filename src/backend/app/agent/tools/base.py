from __future__ import annotations

from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from typing import Any, Literal, Protocol

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.agent.schemas.parts import ArtifactRef, ToolEstimate


class ToolOutcome(BaseModel):
    result: dict[str, Any]
    artifact: ArtifactRef | None = None
    degraded: bool = False


class ToolServices(BaseModel):
    """Runtime services injected by the harness — never part of model args."""

    model_config = {"arbitrary_types_allowed": True}

    uow: Any = None
    patcher: Any = None
    conversation_id: str | None = None
    emit: Callable[[dict[str, Any]], Awaitable[None]] | None = None
    on_tool_pending: Callable[..., Awaitable[None]] | None = None
    on_awaiting_confirmation: Callable[..., Awaitable[None]] | None = None
    on_tool_running: Callable[..., Awaitable[None]] | None = None
    on_tool_error: Callable[..., Awaitable[None]] | None = None
    on_tool_completed: Callable[..., Awaitable[None]] | None = None


class TaskTool(Protocol):
    async def estimate(self, args: BaseModel, services: ToolServices) -> ToolEstimate: ...

    async def run(self, args: BaseModel, services: ToolServices) -> ToolOutcome: ...


class QueryHandler(Protocol):
    async def run(self, args: BaseModel, services: ToolServices) -> dict[str, Any]: ...


class ToolSpec(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    name: str
    description: str
    input_model: type[BaseModel]
    kind: Literal["query", "task"]
    confirmation: Literal["never", "over_threshold", "always"] = "never"
    render: str | None = None
    handler: Any


class ToolRegistry:
    def __init__(self) -> None:
        self._specs: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        self._specs[spec.name] = spec

    def get(self, name: str) -> ToolSpec:
        if name not in self._specs:
            raise KeyError(f"Unknown tool: {name}")
        return self._specs[name]

    def all(self) -> list[ToolSpec]:
        return list(self._specs.values())

    def tools_blurb(self) -> str:
        if not self._specs:
            return "(no tools registered)"
        lines = ["Available tools:"]
        for spec in self._specs.values():
            lines.append(f"- {spec.name}: {spec.description}")
        return "\n".join(lines)


_REGISTRY = ToolRegistry()
_SERVICES: ContextVar[ToolServices | None] = ContextVar(
    "agent_tool_services",
    default=None,
)


def get_tool_registry() -> ToolRegistry:
    return _REGISTRY


def register_tool(spec: ToolSpec) -> None:
    _REGISTRY.register(spec)


def set_tool_services(services: ToolServices):
    return _SERVICES.set(services)


def reset_tool_services(token) -> None:
    _SERVICES.reset(token)


def get_tool_services() -> ToolServices:
    services = _SERVICES.get()
    if services is None:
        raise RuntimeError("Tool services not bound for this turn")
    return services


def langchain_tools(registry: ToolRegistry | None = None) -> list[StructuredTool]:
    """Generate LangChain tools from ToolSpecs — one schema, one source of truth."""
    registry = registry or _REGISTRY
    tools: list[StructuredTool] = []

    for spec in registry.all():
        async def _run(
            __spec: ToolSpec = spec,
            **kwargs: Any,
        ) -> str:
            services = get_tool_services()
            args = __spec.input_model.model_validate(kwargs)
            if __spec.kind == "query":
                result = await __spec.handler.run(args, services)
                return str(result)

            # Task tools: estimate/confirm is owned by EstimateConfirmMiddleware.
            # By the time we reach here, confirmation already happened (or was skipped).
            outcome: ToolOutcome = await __spec.handler.run(args, services)
            return str(outcome.result)

        tools.append(
            StructuredTool.from_function(
                coroutine=_run,
                name=spec.name,
                description=spec.description,
                args_schema=spec.input_model,
            ),
        )
    return tools


def needs_confirmation(spec: ToolSpec, estimate: ToolEstimate, limit: int) -> bool:
    if estimate.over_cap:
        return False  # refuse path, not confirm
    if spec.confirmation == "always":
        return True
    if spec.confirmation == "never":
        return False
    # over_threshold
    return estimate.llm_calls > limit
