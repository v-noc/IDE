# 02 — LLM Provider Layer

The requirement: the model provider must be **chooseable/configurable** — OpenAI,
Vercel AI Gateway, or any OpenAI-compatible endpoint — and **hardcoded for now**
(a settings default, no UI). This file is the whole design.

## The key insight: one client, a registry of endpoints

Every provider we care about speaks the OpenAI chat-completions protocol:

| Provider | Base URL | Models we'd use |
|---|---|---|
| `openai` | (SDK default) | `gpt-4o-mini`, … |
| `vercel` (AI Gateway) | `https://ai-gateway.vercel.sh/v1` | `zai/glm-4.7`, `moonshotai/kimi-k2.5`, one key for all |
| `custom` | anything from settings | GLM/Kimi direct endpoints, OpenRouter, LM Studio/vLLM local |
| `fake` | none (no network) | deterministic canned outputs for tests/dev (05) |

So the "provider abstraction" is **not** an interface over N SDKs (that was Eregna's
problem — it needed Claude-specific streaming). It is one `ChatOpenAI` class pointed
at different base URLs. A genuinely different SDK later (Anthropic, Gemini) becomes a
new branch inside `factory.py` — one file, callers unchanged.

## providers.py — the registry

```python
@dataclass(frozen=True)
class ProviderSpec:
    name: str
    base_url: str | None          # None = OpenAI default
    api_key_env: str              # which settings field holds the key
    default_model: str

PROVIDERS: dict[str, ProviderSpec] = {
    "openai": ProviderSpec("openai", None, "OPENAI_API_KEY", "gpt-4o-mini"),
    "vercel": ProviderSpec("vercel", "https://ai-gateway.vercel.sh/v1",
                           "AI_GATEWAY_API_KEY", "zai/glm-4.7"),
    "custom": ProviderSpec("custom", "<from settings>", "CUSTOM_LLM_API_KEY", "<from settings>"),
    "fake":   ProviderSpec("fake", None, "", "fake-model"),
}
```

## Settings (hardcoded-for-now lives here)

```python
# app/config/settings.py — added fields
WALKTHROUGH_LLM_PROVIDER: str = "vercel"          # ← the hardcoded choice
WALKTHROUGH_LLM_MODEL: Optional[str] = None       # None → provider's default_model
OPENAI_API_KEY: Optional[str] = None
AI_GATEWAY_API_KEY: Optional[str] = None
CUSTOM_LLM_BASE_URL: Optional[str] = None
CUSTOM_LLM_API_KEY: Optional[str] = None
```

"Hardcoded" means: the default value in `Settings` decides; `.env` can override; no
request or UI can. When per-tour model choice arrives later, `RunRequest` gains an
optional `model` field that shadows the setting inside `make_chat` — a five-line
change, and the seam is documented here so nobody invents a second path.

Startup validation (in `get_settings()` consumers, fail fast): unknown provider name →
error at boot; missing key for the chosen provider → error at boot, not at first call.
The `fake` provider requires nothing — a fresh checkout runs.

## factory.py — make_chat

Per-call-type parameters come from the parent plan (05) and live here as one table:

```python
CALL_PARAMS = {
    "intro":      dict(temperature=0.5, max_tokens=300),
    "block_plan": dict(temperature=0.2, max_tokens=400),
    "block_text": dict(temperature=0.5, max_tokens=350),
}

def make_chat(call_type: str) -> BaseChatModel:
    s = get_settings()
    spec = PROVIDERS[s.WALKTHROUGH_LLM_PROVIDER]
    if spec.name == "fake":
        return FakeChatModel(call_type=call_type)          # 05
    return ChatOpenAI(
        model=s.WALKTHROUGH_LLM_MODEL or spec.default_model,
        base_url=resolve_base_url(spec, s),
        api_key=resolve_key(spec, s),
        **CALL_PARAMS[call_type],
        timeout=60, max_retries=1,                          # transport-level retries
    )
```

`model_id` recorded on the session (parent 04) is `f"{provider}:{model}"` so eval
fixtures always say what produced them.

## structured.py — the one way we call a model

Every pipeline call goes through a single helper implementing the uniform failure
policy (parent 05):

```python
async def structured_call(
    call_type: str,
    schema: type[BaseModel],           # BlockPlan, IntroOut, BlockTextOut
    system: str,
    user: str,
    validate: Callable[[BaseModel], list[str]],   # extra code-side rules; [] = ok
) -> tuple[BaseModel | None, list[str]]:          # (result, error_log_lines)
```

Behavior:

1. `make_chat(call_type).with_structured_output(schema, method="json_mode")` — JSON
   mode, **not** tool calling: broadest compatibility across GLM/Kimi/gateway
   endpoints, and it sidesteps the known small-model quirks Eregna hit (parallel tool
   calls breaking structured output; strict-mode optional fields; reasoning tokens
   leaking into the tool channel).
2. Parse + run `validate`. On failure: **one retry** with the exact error appended to
   the user message.
3. On second failure: return `(None, errors)` — the **caller** applies its
   deterministic fallback (`fallbacks.py`). The helper never invents content.
4. Every attempt logs one loguru line: call_type, node_id (from contextvars), attempt,
   latency, token usage; usage accumulates on the session.

Schemas keep the CoT contract from parent 08: `reasoning` fields **first** in field
order, and JSON-mode prompts restate the schema in words (parent 07's OUTPUT layer)
because JSON mode enforces JSON-ness, not the exact shape — the validator is the real
gate either way.

## What this layer deliberately does not do

- No streaming interfaces — texts arrive whole (parent 04).
- No provider fallback chains ("try vercel, then openai") — silent model switching
  mid-tour makes evals meaningless. If the provider is down, the run fails honestly.
- No token-budget accounting beyond recording usage — cost control is the estimate +
  the over-cap gate (parent 03).
- No secrets in logs or sessions: key values never leave settings; `model_id` is
  name+model only.
