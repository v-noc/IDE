from __future__ import annotations

from dataclasses import dataclass

from app.config.settings import Settings, get_settings


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    base_url: str | None
    api_key_field: str
    default_model: str
    models: tuple[str, ...] = ()


PROVIDERS: dict[str, ProviderSpec] = {
    "openai": ProviderSpec(
        "openai",
        None,
        "OPENAI_API_KEY",
        "gpt-4o-mini",
        models=("gpt-4o-mini",),
    ),
    "vercel": ProviderSpec(
        "vercel",
        "https://ai-gateway.vercel.sh/v1",
        "AI_GATEWAY_API_KEY",
        "zai/glm-4.7",
        models=("zai/glm-4.7", "moonshotai/kimi-k2.5"),
    ),
    "custom": ProviderSpec(
        "custom",
        None,
        "CUSTOM_LLM_API_KEY",
        "custom-model",
    ),
    "fake": ProviderSpec("fake", None, "", "fake-model"),
}


@dataclass(frozen=True)
class ResolvedLLM:
    spec: ProviderSpec
    model: str
    model_id: str


def parse_llm_spec(value: str) -> tuple[str, str | None]:
    """'vercel:zai/glm-4.7' -> ('vercel', 'zai/glm-4.7'); 'fake' -> ('fake', None)."""
    provider, _, model = value.strip().partition(":")
    return provider, (model or None)


def resolve_llm(
    override: str | None = None,
    settings: Settings | None = None,
) -> ResolvedLLM:
    """Resolve provider+model. Order: override → WALKTHROUGH_LLM model → default."""
    settings = settings or get_settings()
    raw = (settings.WALKTHROUGH_LLM or "").strip()
    if not raw:
        raise ValueError(
            "WALKTHROUGH_LLM is empty — set e.g. 'fake' or 'openai:gpt-4o-mini'",
        )

    provider_name, model_from_spec = parse_llm_spec(raw)
    if not provider_name or provider_name not in PROVIDERS:
        raise ValueError(
            f"Unknown walkthrough LLM provider in {raw!r}. "
            f"Known: {', '.join(sorted(PROVIDERS))}",
        )

    spec = PROVIDERS[provider_name]
    model = override or model_from_spec or spec.default_model
    return ResolvedLLM(spec=spec, model=model, model_id=f"{spec.name}:{model}")


def resolve_model_id(
    override: str | None = None,
    settings: Settings | None = None,
) -> str:
    return resolve_llm(override=override, settings=settings).model_id


def validate_llm_settings(settings: Settings | None = None) -> ResolvedLLM:
    """Fail at boot for malformed spec / unknown provider / missing key."""
    settings = settings or get_settings()
    resolved = resolve_llm(settings=settings)
    spec = resolved.spec

    if spec.name == "fake":
        return resolved

    if not spec.api_key_field:
        return resolved

    key = getattr(settings, spec.api_key_field, None)
    if not key:
        raise ValueError(
            f"WALKTHROUGH_LLM={settings.WALKTHROUGH_LLM!r} needs "
            f"{spec.api_key_field} set, or change WALKTHROUGH_LLM to 'fake'",
        )

    if spec.name == "custom" and not settings.CUSTOM_LLM_BASE_URL:
        raise ValueError(
            "WALKTHROUGH_LLM=custom requires CUSTOM_LLM_BASE_URL — "
            "set it or change WALKTHROUGH_LLM",
        )

    return resolved


def models_catalog(settings: Settings | None = None) -> dict:
    """Shape for GET /walkthroughs/models — never includes key values."""
    settings = settings or get_settings()
    active = resolve_llm(settings=settings)
    providers = []
    for name, spec in PROVIDERS.items():
        if name == "fake" and active.spec.name != "fake":
            continue
        configured = True
        if spec.api_key_field:
            configured = bool(getattr(settings, spec.api_key_field, None))
        providers.append(
            {
                "name": name,
                "configured": configured,
                "default_model": spec.default_model,
                "models": list(spec.models),
            },
        )
    return {"active": active.model_id, "providers": providers}


@dataclass(frozen=True)
class ReasoningCaps:
    channel: str  # exposed | summary | none
    effort_param: str | None  # reasoning_effort | budget_tokens | thinking_flag | None
    always_on: bool = False


REASONING_BY_MODEL: dict[str, ReasoningCaps] = {
    "gpt-5": ReasoningCaps("summary", "reasoning_effort", always_on=True),
    "o1": ReasoningCaps("summary", "reasoning_effort", always_on=True),
    "o3": ReasoningCaps("summary", "reasoning_effort", always_on=True),
    "zai/glm": ReasoningCaps("exposed", "thinking_flag"),
    "moonshotai/kimi": ReasoningCaps("exposed", "thinking_flag"),
}


def reasoning_caps_for(model: str) -> ReasoningCaps:
    for prefix, caps in REASONING_BY_MODEL.items():
        if model.startswith(prefix) or prefix in model:
            return caps
    return ReasoningCaps("none", None)


def effort_overrides(model: str, effort: str) -> dict:
    """Map off|low|medium|high → provider-specific ChatOpenAI kwargs."""
    caps = reasoning_caps_for(model)
    if caps.effort_param is None or effort == "off" and not caps.always_on:
        return {}

    if caps.effort_param == "reasoning_effort":
        mapped = {
            "off": "minimal",
            "low": "low",
            "medium": "medium",
            "high": "high",
        }.get(effort, "medium")
        return {"extra_body": {"reasoning_effort": mapped}}

    if caps.effort_param == "thinking_flag":
        if effort == "off":
            return {"extra_body": {"thinking": {"type": "disabled"}}}
        return {"extra_body": {"thinking": {"type": "enabled"}}}

    return {}


def resolve_agent_llm(
    override: str | None = None,
    settings: Settings | None = None,
) -> ResolvedLLM:
    """Resolve agent model: AGENT_LLM → WALKTHROUGH_LLM → default."""
    settings = settings or get_settings()
    raw = (settings.AGENT_LLM or settings.WALKTHROUGH_LLM or "").strip()
    if not raw:
        raise ValueError(
            "AGENT_LLM / WALKTHROUGH_LLM empty — set e.g. 'fake' or "
            "'openai:gpt-4o-mini'",
        )

    provider_name, model_from_spec = parse_llm_spec(raw)
    if not provider_name or provider_name not in PROVIDERS:
        raise ValueError(
            f"Unknown agent LLM provider in {raw!r}. "
            f"Known: {', '.join(sorted(PROVIDERS))}",
        )

    spec = PROVIDERS[provider_name]
    model = override or model_from_spec or spec.default_model
    return ResolvedLLM(spec=spec, model=model, model_id=f"{spec.name}:{model}")


MODEL_OVERRIDES: dict[str, dict] = {
    "gpt-5": {"extra_body": {"reasoning_effort": "low"}},
}


def overrides_for(model: str) -> dict:
    for prefix, extra in MODEL_OVERRIDES.items():
        if model.startswith(prefix):
            return extra
    return {}
