# 02 — LLM Provider Layer

The requirement, revised 2026-07-11: switching provider or model must be **one edit in
one place, no code changes**; adding a new provider or model must cost **at most one
line**; the default must be obvious; and the shape must already fit a later
user-facing model picker so that feature is additive, not a rewrite. This file is the
whole design.

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
new branch inside `make_chat` — one file, callers unchanged.

## One knob: `WALKTHROUGH_LLM = "provider:model"`

Revision 1 had two settings (`WALKTHROUGH_LLM_PROVIDER` + `WALKTHROUGH_LLM_MODEL`).
Two knobs for one decision invite the split-brain config (provider says `vercel`,
model says `gpt-4o-mini`). One string, one decision:

```bash
WALKTHROUGH_LLM="fake"                        # provider only → its default model
WALKTHROUGH_LLM="vercel"                      # → zai/glm-4.7 (vercel's default)
WALKTHROUGH_LLM="vercel:moonshotai/kimi-k2.5"
WALKTHROUGH_LLM="openai:gpt-4o-mini"
WALKTHROUGH_LLM="custom:llama3:8b"            # + CUSTOM_LLM_BASE_URL in settings
```

Parsing splits on the **first** colon only — model ids may themselves contain colons
(Ollama tags like `llama3:8b`) and slashes (gateway ids like `zai/glm-4.7`).

**Switching is editing this one `.env` line and restarting.** Nothing else moves:
prompts, pipeline, session stamping are all downstream of one resolver (below).

## providers.py — the registry (one line per provider)

```python
@dataclass(frozen=True)
class ProviderSpec:
    name: str
    base_url: str | None            # None = OpenAI SDK default
    api_key_field: str              # which Settings field holds the key; "" = keyless
    default_model: str              # used when the spec string names no model
    models: tuple[str, ...] = ()    # curated list for the FUTURE PICKER — display
                                    # only, NOT a whitelist (see below)

PROVIDERS: dict[str, ProviderSpec] = {
    "openai": ProviderSpec("openai", None, "OPENAI_API_KEY", "gpt-4o-mini",
                           models=("gpt-4o-mini",)),
    "vercel": ProviderSpec("vercel", "https://ai-gateway.vercel.sh/v1",
                           "AI_GATEWAY_API_KEY", "zai/glm-4.7",
                           models=("zai/glm-4.7", "moonshotai/kimi-k2.5")),
    "custom": ProviderSpec("custom", None, "CUSTOM_LLM_API_KEY", "custom-model"),
    "fake":   ProviderSpec("fake", None, "", "fake-model"),
}
```

The cost of every future change, measured:

| Change | Cost |
|---|---|
| Try a new model on an existing provider | **zero code** — write it in `WALKTHROUGH_LLM` |
| Add that model to the future picker's list | one string in `models=` |
| Change a provider's default model | one string in `default_model=` |
| Add a new OpenAI-compatible provider | one `PROVIDERS` line (+ one `Settings` key field if it needs its own key) |
| Add a non-OpenAI SDK (Anthropic, Gemini) | one branch in `make_chat`; registry line same as above; callers unchanged |

Why `models` is display-only and never a validation whitelist: gateways add models
weekly, and a whitelist would turn the registry into a chore and block quick
experiments — exactly what this revision exists to avoid. A typo'd model id fails at
the first call with the provider's own 404/400, which lands in the normal error path
(`end` frame with the message). Boot-time cannot verify remote model ids anyway.

## resolve.py — one resolver, every consumer (the picker seam)

```python
@dataclass(frozen=True)
class ResolvedLLM:
    spec: ProviderSpec
    model: str
    model_id: str        # "vercel:zai/glm-4.7" — stamped on every session (04)

def resolve_llm(
    override: str | None = None,      # the future per-request choice; today: None
    settings: Settings | None = None,
) -> ResolvedLLM:
    ...
```

Resolution order — the whole future picker feature is already this list:

```
1. override            ← later: RunRequest.model, sent by the UI picker
2. the model part of WALKTHROUGH_LLM
3. the provider's default_model
```

Every consumer goes through `resolve_llm` — `make_chat`, the session's `model_id`
stamp in the service, and startup validation. **Nobody reads the settings fields
directly.** That discipline is what makes the picker a five-line feature later:
`RunRequest` gains `model: str | None = None`, the service passes it as `override`,
done — no other file changes, and sessions already record which model produced them.

## Settings

```python
# app/config/settings.py
WALKTHROUGH_LLM: str = "fake"        # provider[:model] — the ONLY switch
OPENAI_API_KEY: Optional[str] = None
AI_GATEWAY_API_KEY: Optional[str] = None
CUSTOM_LLM_BASE_URL: Optional[str] = None
CUSTOM_LLM_API_KEY: Optional[str] = None
```

The default is `fake` on purpose (the code already chose this over rev 1's `vercel`,
and it was right): a fresh checkout runs keyless — tests, CI, and the frontend demo
need no secrets. Real providers are a `.env` concern, never a code default.

Startup validation (fail at **boot**, not at stop 3 of a user's first tour):
malformed spec string, unknown provider name, missing key for the chosen provider,
`custom` without `CUSTOM_LLM_BASE_URL`. The one thing boot cannot check is whether
the model id exists remotely — that fails honestly at the first call.

## GET /walkthrough/models — the picker's API (endpoint now, UI later)

Ten lines on the existing router, so the future picker is a frontend-only feature:

```json
{
  "active": "vercel:zai/glm-4.7",
  "providers": [
    {"name": "vercel", "configured": true,
     "default_model": "zai/glm-4.7",
     "models": ["zai/glm-4.7", "moonshotai/kimi-k2.5"]},
    {"name": "openai", "configured": false,
     "default_model": "gpt-4o-mini", "models": ["gpt-4o-mini"]}
  ]
}
```

- `configured` = "this provider's key field is set" — a boolean, **never** the key.
  The picker can gray out providers the deployment has no key for.
- `fake` is listed only when it is the active provider (it exists for dev, not for
  users to pick).
- The UI, when it comes, reads this, renders a select, and puts the choice in
  `RunRequest.model`. Nothing else.

## Per-model quirks — a documented seam, empty for MVP

Some models need special handling with JSON mode (Eregna v2's fixes folder documents
GLM/Kimi reasoning tokens leaking into the JSON channel, parallel-tool-call breakage,
strict-mode optional fields). When that lands, it goes here — keyed by model-id
prefix, merged into the client kwargs, **zero changes at call sites**:

```python
MODEL_OVERRIDES: dict[str, dict] = {
    # "zai/":        {"extra_body": {...disable thinking mode...}},
    # "moonshotai/": {...},
    # "gpt-5":       {"reasoning_effort": "low"},   # tame hidden-reasoning spend
}
```

Reasoning models are the first real customer of this seam: their hidden thinking is
paid output tokens on every one of our ~35 calls per tour, and some reject or ignore
`temperature`. Tuning that (e.g. `reasoning_effort`) is a per-model-prefix override
here — never a change to `CALL_PARAMS` or the call sites.

Empty today. The point of writing the empty dict into the plan: the next person with
a model quirk has a place to put it that isn't an `if` inside the pipeline.

## make_chat — the factory

Per-call-type parameters live here as one table:

```python
# NO completion caps — deliberate (learned live, 2026-07-11). Reasoning models
# (gpt-5 family, o-series, GLM/Kimi thinking modes) spend max_tokens on hidden
# reasoning FIRST: observed reasoning_tokens=700 of a 700 cap, zero content,
# every intro failing "length limit reached". A cap sized for one model family
# starves another, and machine-truncated prose is never acceptable output.
# Length is steered by the prompts ("aim for 2-4 sentences" — a target, not a
# limit); cost is controlled by the tour-level estimate + visit cap (03), never
# by cutting a generation mid-thought.
CALL_PARAMS = {
    "intro":      dict(temperature=0.5),
    "block_plan": dict(temperature=0.2),
    "block_text": dict(temperature=0.5),
}

def make_chat(call_type: str, override: str | None = None) -> BaseChatModel:
    r = resolve_llm(override)
    if r.spec.name == "fake":
        return FakeChatModel(call_type=call_type)          # 05
    return ChatOpenAI(
        model=r.model,
        base_url=r.spec.base_url or custom_base_url_from_settings(r.spec),
        api_key=read_key(r.spec),
        **CALL_PARAMS[call_type],
        **overrides_for(r.model),                          # MODEL_OVERRIDES
        timeout=60, max_retries=1,                          # transport-level retries
    )
```

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
   leaking into the tool channel). One hard prerequisite of `json_object`: **the
   messages must contain the literal word "json"** or OpenAI rejects the request
   with a 400 before generating anything. That guarantee lives in the prompts (07's
   OUTPUT layer: "You return one JSON object…") plus a prompt unit test — never in
   this layer.
2. Parse + run `validate`. On failure: **one retry** with the exact error appended to
   the user message. There is **no length/finish_reason policing** — we set no
   completion cap, so nothing of ours can cut a response. If a provider's own hard
   limit ever truncates one, the JSON fails to parse and lands in this same retry →
   fallback path; no special case needed.
3. On second failure: return `(None, errors)` — the **caller** applies its
   deterministic fallback (`fallbacks.py`). The helper never invents content.
4. Every attempt logs one loguru line: call_type, node_id (from contextvars), attempt,
   latency, token usage; usage accumulates on the session.

Schemas keep the CoT contract from parent 08: `reasoning` fields **first** in field
order (and for the block plan, `block_count` before `blocks` — the commitment field),
and JSON-mode prompts restate the schema in words (parent 07's OUTPUT layer) because
JSON mode enforces JSON-ness, not the exact shape — the validator is the real gate
either way.

One boundary note: `system` and `user` arrive here as **rendered strings**. The
`ChatPromptTemplate` objects (parent 07 Part 1) live and die inside `prompts.py` —
this layer, the `FakeLLM`, and the logging never see a template, so swapping prompt
internals never touches the provider layer. The same holds the other way: swapping
provider or model never touches a prompt.

## What this layer deliberately does not do

- No streaming interfaces — texts arrive whole (parent 04).
- No provider fallback chains ("try vercel, then openai") — silent model switching
  mid-tour makes evals meaningless (`model_id` on the session would lie). If the
  provider is down, the run fails honestly.
- No per-call-type model choice for now — one model per tour. The seam exists
  (`make_chat(call_type, override)`) but no config drives it until evals show a
  reason (e.g. a cheaper model for block texts).
- No model whitelisting — see the registry section.
- No token-budget accounting beyond recording usage — cost control is the estimate +
  the over-cap gate (parent 03).
- No secrets in logs, sessions, or the `/models` endpoint: key values never leave
  settings; `model_id` is name+model only, `configured` is a boolean.
