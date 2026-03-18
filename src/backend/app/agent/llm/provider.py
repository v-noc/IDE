from abc import ABC, abstractmethod
from typing import Any, AsyncIterator
from langchain_core.messages import BaseMessage


class LLMProvider(ABC):
    """Abstract interface for an LLM provider."""

    name: str       # e.g. "openai", "anthropic", "local"
    model: str      # e.g. "gpt-4o", "claude-3-sonnet"

    @abstractmethod
    async def invoke(
        self,
        messages: list[BaseMessage],
        **kwargs,
    ) -> BaseMessage:
        """Single-shot invocation. Returns one complete message."""
        ...

    @abstractmethod
    async def stream(
        self,
        messages: list[BaseMessage],
        **kwargs,
    ) -> AsyncIterator[str]:
        """Streaming invocation. Yields token chunks."""
        ...

    @abstractmethod
    def supports_tools(self) -> bool:
        """Does this provider support native tool/function calling?"""
        ...

    @abstractmethod
    def max_context_tokens(self) -> int:
        """Maximum context window size for this model."""
        ...
