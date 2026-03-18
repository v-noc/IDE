
from fastapi import Request
from app.agent.runner.executor import AgentExecutor
from app.agent.models.conversation_store import InMemoryConversationStore


def get_agent_executor(request: Request) -> AgentExecutor:
    """Dependency to get the global AgentExecutor."""
    if not hasattr(request.app.state, "agent_executor"):
        raise RuntimeError("Agent executor not initialized in app state.")
    return request.app.state.agent_executor


def get_conversation_store(request: Request) -> InMemoryConversationStore:
    """Dependency to get the global Conversation Store."""
    if not hasattr(request.app.state, "conversation_store"):
        raise RuntimeError("Conversation store not initialized in app state.")
    return request.app.state.conversation_store
