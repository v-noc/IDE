from langchain_openai import ChatOpenAI
from app.agent.llm.provider import LLMProvider
from typing import AsyncIterator
from langchain_core.messages import BaseMessage


class OpenAIProvider(LLMProvider):
    name = "openai"

    MODEL_CONTEXTS = {
        "gpt-4o": 128_000,
        "gpt-4o-mini": 128_000,
        "gpt-4-turbo": 128_000,
        "gpt-3.5-turbo": 16_385,
    }

    def __init__(self, model: str = "gpt-4o-mini", **kwargs):
        self.model = model
        self._llm = ChatOpenAI(model=model, **kwargs)

    async def invoke(
        self,
        messages: list[BaseMessage],
        **kwargs,
    ) -> BaseMessage:
        return await self._llm.ainvoke(messages, **kwargs)

    async def stream(
        self,
        messages: list[BaseMessage],
        **kwargs,
    ):
        async for chunk in self._llm.astream(messages, **kwargs):
            if chunk.content:
                yield chunk.content

    def supports_tools(self) -> bool:
        return True

    def max_context_tokens(self) -> int:
        return self.MODEL_CONTEXTS.get(self.model, 128_000)

    @classmethod
    def supported_models(cls) -> list[str]:
        return list(cls.MODEL_CONTEXTS.keys())
