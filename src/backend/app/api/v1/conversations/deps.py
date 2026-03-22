"""FastAPI dependencies for conversation + task APIs."""

from __future__ import annotations

from fastapi import Depends, Request

from app.agent.context.graph_traversal import GraphTraversal
from app.agent.runner.task_manager import TaskManager
from app.api.dependencies import (
    get_project_conversation_repo as get_conversation_repo,
    get_project_conversation_store as get_conversation_store,
    get_project_uow,
)
from app.db.context import ProjectUoW

__all__ = [
    "get_conversation_repo",
    "get_conversation_store",
    "get_graph_traversal",
    "get_task_manager",
]


def get_task_manager(request: Request) -> TaskManager:
    tm = getattr(request.app.state, "task_manager", None)
    if tm is None:
        raise RuntimeError("task_manager not initialized on app.state")
    return tm


def get_graph_traversal(
    uow: ProjectUoW = Depends(get_project_uow),
) -> GraphTraversal:
    """Graph access scoped to the resolved project, branch, and ref."""
    return GraphTraversal(uow)
