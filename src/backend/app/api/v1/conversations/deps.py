"""FastAPI dependencies for conversation + task APIs."""

from __future__ import annotations

from fastapi import Request

from app.agent.runner.executor import AgentExecutor
from app.agent.runner.task_manager import TaskManager
from app.api.dependencies import (
    get_project_conversation_repo as get_conversation_repo,
    get_project_conversation_store as get_conversation_store,
)

__all__ = [
    "get_agent_executor",
    "get_conversation_repo",
    "get_conversation_store",
    "get_task_manager",
]


def get_task_manager(request: Request) -> TaskManager:
    tm = getattr(request.app.state, "task_manager", None)
    if tm is None:
        raise RuntimeError("task_manager not initialized on app.state")
    return tm


def get_agent_executor(request: Request) -> AgentExecutor:
    ex = getattr(request.app.state, "agent_executor", None)
    if ex is None:
        raise RuntimeError("agent_executor not initialized on app.state")
    return ex
