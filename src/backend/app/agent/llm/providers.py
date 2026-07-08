from __future__ import annotations

from dataclasses import dataclass

from app.config.settings import Settings, get_settings


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    base_url: str | None
    api_key_field: str
    default_model: str


PROVIDERS: dict[str, ProviderSpec] = {
    "openai": ProviderSpec("openai", None, "OPENAI_API_KEY", "gpt-4o-mini"),
    "vercel": ProviderSpec(
        "vercel",
        "https://ai-gateway.vercel.sh/v1",
        "AI_GATEWAY_API_KEY",
        "zai/glm-4.7",
    ),
    "custom": ProviderSpec("custom", None, "CUSTOM_LLM_API_KEY", "custom-model"),
    "fake": ProviderSpec("fake", None, "", "fake-model"),
}


def resolve_provider(settings: Settings | None = None) -> ProviderSpec:
    settings = settings or get_settings()
    name = settings.WALKTHROUGH_LLM_PROVIDER
    if name not in PROVIDERS:
        raise ValueError(f"Unknown walkthrough LLM provider: {name}")
    return PROVIDERS[name]


def resolve_model_id(settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    spec = resolve_provider(settings)
    model = settings.WALKTHROUGH_LLM_MODEL or spec.default_model
    return f"{spec.name}:{model}"
