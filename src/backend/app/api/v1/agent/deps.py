from fastapi import Depends, Request

from app.agent.context.graph_traversal import GraphTraversal
from app.agent.runner.executor import AgentExecutor
from app.api.dependencies import get_project_uow
from app.db.context import ProjectUoW


def get_agent_executor(request: Request) -> AgentExecutor:
    """Dependency to get the global AgentExecutor."""
    if not hasattr(request.app.state, "agent_executor"):
        raise RuntimeError("Agent executor not initialized in app state.")
    return request.app.state.agent_executor


def get_graph_traversal(
    uow: ProjectUoW = Depends(get_project_uow),
) -> GraphTraversal:
    """Graph access scoped to the resolved project, branch, and ref (see RequestDbContext)."""
    return GraphTraversal(uow)
