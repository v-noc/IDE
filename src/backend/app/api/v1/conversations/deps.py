"""FastAPI dependencies for conversation + task APIs."""

from __future__ import annotations

from fastapi import Request

from app.agent.runner.executor import AgentExecutor
from app.agent.runner.task_manager import TaskManager
from app.agent.conversation_store import ConversationStore
from app.core.repository.conversation import ConversationRepo


def get_conversation_repo(request: Request) -> ConversationRepo:
    repo = getattr(request.app.state, "conversation_repo", None)
    if repo is None:
        raise RuntimeError("conversation_repo not initialized on app.state")
    return repo


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


def get_conversation_store(request: Request) -> ConversationStore:
    st = getattr(request.app.state, "conversation_store", None)
    if st is None:
        raise RuntimeError("conversation_store not initialized on app.state")
    return st
