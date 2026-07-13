from __future__ import annotations

from langchain_openai import ChatOpenAI

from app.agent.llm.providers import (
    effort_overrides,
    overrides_for,
    resolve_agent_llm,
)
from app.agent.schemas.conversation import EffortLevel
from app.config.settings import Settings, get_settings

# Orchestrator: no completion cap (same lesson as walkthrough micro-calls).
AGENT_CALL_PARAMS = {"temperature": 0.4}


def build_agent_model(
    *,
    effort: EffortLevel | None = None,
    settings: Settings | None = None,
) -> tuple[ChatOpenAI | None, str]:
    """Return (chat_model, model_id). model is None when provider is fake."""
    settings = settings or get_settings()
    resolved = resolve_agent_llm(settings=settings)

    if resolved.spec.name == "fake":
        return None, resolved.model_id

    api_key = None
    if resolved.spec.api_key_field:
        api_key = getattr(settings, resolved.spec.api_key_field, None)
        if not api_key:
            raise ValueError(
                f"Missing {resolved.spec.api_key_field} for provider "
                f"{resolved.spec.name!r}",
            )

    base_url = resolved.spec.base_url
    if resolved.spec.name == "custom":
        base_url = settings.CUSTOM_LLM_BASE_URL
        if not base_url:
            raise ValueError(
                "CUSTOM_LLM_BASE_URL is required for provider 'custom'",
            )

    applied_effort = effort or settings.AGENT_REASONING_EFFORT  # type: ignore[assignment]
    if applied_effort not in ("off", "low", "medium", "high"):
        applied_effort = "medium"

    extra = {
        **AGENT_CALL_PARAMS,
        **overrides_for(resolved.model),
        **effort_overrides(resolved.model, applied_effort),
    }

    chat = ChatOpenAI(
        model=resolved.model,
        base_url=base_url,
        api_key=api_key,
        timeout=120,
        max_retries=1,
        **extra,
    )
    return chat, resolved.model_id
