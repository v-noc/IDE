# agent/llm/gateway.py

from dataclasses import dataclass
from app.agent.chat.completion_params import ChatCompletionParams
from app.agent.config import settings


@dataclass
class ResolvedLLM:
    provider: object  # the LangChain-compatible provider
    model: str
    provider_name: str


class LLMGateway:
    """Single responsibility: resolve params → usable LLM instance."""

    def __init__(self, llm_factory):
        self._factory = llm_factory

    def resolve(
        self, params: ChatCompletionParams | None = None
    ) -> ResolvedLLM:
        params = params or ChatCompletionParams()
        model = params.model or settings.default_model
        provider_name = params.provider or settings.default_provider
        extra = params.provider_create_kwargs()

        mt = extra.get("max_tokens")
        if mt is not None and mt > settings.max_total_tokens:
            extra["max_tokens"] = settings.max_total_tokens

        llm = self._factory.create(
            provider=provider_name, model=model, **extra
        )
        return ResolvedLLM(
            provider=llm, model=model, provider_name=provider_name
        )

    def create_mini(self) -> object:
        """Cheap model for metadata generation."""
        return self._factory.create(model="gpt-4o-mini")
