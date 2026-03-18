from app.agent.llm.provider import LLMProvider
from app.agent.config import AgentConfig


class LLMFactory:
    """Create LLM provider instances based on configuration."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self._providers: dict[str, type[LLMProvider]] = {}

    def register_provider(
        self,
        name: str,
        provider_cls: type[LLMProvider],

    ):
        self._providers[name] = provider_cls

    def create(
        self,
        *,
        provider: str | None = None,
        model: str | None = None,
        **kwargs,
    ) -> LLMProvider:
        provider = provider or self.config.default_provider  # e.g. "openai"
        model = model or self.config.default_model            # e.g. "gpt-4o"
        provider_cls = self._providers[provider]

        return provider_cls(model=model, **kwargs)

    def list_available(self) -> list[dict]:
        """List registered providers and their supported models."""
        return [
            {"provider": name, "models": cls.supported_models()}
            for name, cls in self._providers.items()
        ]
