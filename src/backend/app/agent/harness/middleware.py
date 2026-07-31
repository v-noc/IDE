from __future__ import annotations

from collections.abc import Awaitable, Callable

from langchain.agents.middleware import (
    AgentMiddleware,
    ModelCallLimitMiddleware,
    ModelRequest,
    ModelResponse,
)
from langchain_core.messages import SystemMessage

from app.agent.context.factory import ContextFactory
from app.agent.context.xml import render_project_header
from app.agent.prompts.registry import get_prompt_registry
from app.agent.prompts.shared import AGENT_PERSONA, GLOSSARY
from app.agent.schemas.parts import NodeRefPart
from app.core.model.nodes import ProjectNode
from app.core.repository import Repositories


class ProjectContextMiddleware(AgentMiddleware):
    """Inject rendered agent.system (with <project>) as the system prompt."""

    def __init__(
        self,
        project: ProjectNode,
        *,
        tools_blurb: str = "",
    ):
        self.project = project
        self.tools_blurb = tools_blurb
        self.prompt_version = get_prompt_registry().version("agent.system")

    def _system_text(self) -> str:
        project_block = render_project_header(
            self.project.name,
            self.project.description or "",
        )
        return get_prompt_registry().render(
            "agent.system",
            persona=AGENT_PERSONA,
            glossary=GLOSSARY,
            project_block=project_block,
            tools=self.tools_blurb or "(no tools registered)",
        )

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        system = SystemMessage(content=self._system_text())
        request = request.override(system_message=system)
        return await handler(request)


class NodeEnrichmentMiddleware(AgentMiddleware):
    """Append <attached_node> blocks for current-turn node_refs.

    Enrichment is primarily done in history.build via attached_blocks.
    This middleware is a safety net: if the last human message has bare
    node cards only, it does nothing (history already expanded).
    """

    def __init__(
        self,
        repos: Repositories,
        node_refs: list[NodeRefPart],
        attached_blocks: dict[str, str],
    ):
        self.repos = repos
        self.node_refs = node_refs
        self.attached_blocks = attached_blocks

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        return await handler(request)


def build_limits_middleware(max_steps: int) -> ModelCallLimitMiddleware:
    return ModelCallLimitMiddleware(run_limit=max_steps)


async def build_attached_blocks(
    repos: Repositories,
    node_refs: list[NodeRefPart],
    *,
    code_loader: Callable[[str], Awaitable[str | None]] | None = None,
) -> dict[str, str]:
    """Build enrichment blocks for ≤3 refs; one-liner cards beyond that."""
    factory = ContextFactory(repos, code_loader=code_loader)
    blocks: dict[str, str] = {}
    if not node_refs:
        return blocks

    full = node_refs[:3]
    code_eligible_ids = [
        r.node_id
        for r in full
        if r.node_type in ("function", "class", "file")
    ]
    allow_code_id = code_eligible_ids[0] if len(code_eligible_ids) == 1 else None

    for ref in full:
        include_code = allow_code_id == ref.node_id
        blocks[ref.node_id] = await factory.build_preset(
            ref.node_id,
            "attached_node",
            include_code=include_code,
        )

    for ref in node_refs[3:]:
        q = f' qname="{ref.qname}"' if ref.qname else ""
        blocks[ref.node_id] = (
            f'<node id="{ref.node_id}" kind="{ref.node_type}" '
            f'name="{ref.name}"{q}/>'
        )
    return blocks
