# 15 — Provider Config: one knob, one resolver, real ChatOpenAI

> Implements the 2026-07-11 revision of `backend/02-llm-provider.md` (canonical —
> read it first). Goal, in the user's words: switch provider or model easily, add a
> new one quickly, set the default simply — and leave the seam ready for a
> user-facing model picker later without rework.
>
> This fix also **wires the real `ChatOpenAI` path** — until now `make_llm` raises
> `NotImplementedError` for everything except `fake`, so "switching" was theoretical.

Follow the README ground rules: open every file before editing, find code by
searching for the quoted snippet, one step at a time, verify by running.

## Reality check (measured 2026-07-11 — re-verify, don't trust)

- `src/backend/app/config/settings.py` — two knobs:
  `WALKTHROUGH_LLM_PROVIDER: str = "fake"` and
  `WALKTHROUGH_LLM_MODEL: Optional[str] = None`. Key fields
  (`OPENAI_API_KEY`, `AI_GATEWAY_API_KEY`, `CUSTOM_LLM_BASE_URL`,
  `CUSTOM_LLM_API_KEY`) already exist.
- `src/backend/app/agent/llm/providers.py` — `ProviderSpec` + `PROVIDERS` registry
  exist (no `models` tuple), plus `resolve_provider()` and `resolve_model_id()`.
- `src/backend/app/agent/llm/structured.py` — `make_llm` returns `FakeLLM` for
  `fake` and **raises `NotImplementedError` for every real provider**.
- Callers of the current functions (grep before you change signatures):
  `app/walkthrough/service.py` (`make_llm("intro")` preflight and
  `resolve_model_id()`), `app/agent/llm/structured.py`.
- `src/backend/app/agent/llm/providers/` — a stale **empty directory** sitting next
  to `providers.py` (only `__pycache__` inside, no `__init__.py`). Python currently
  resolves `app.agent.llm.providers` to the `.py` module, but the shadow dir is a
  trap. Delete it in Step B.
- No startup validation and no `/models` endpoint exist.

---

## Step A — settings: collapse two knobs into one

File: `src/backend/app/config/settings.py`

Find `WALKTHROUGH_LLM_PROVIDER: str = "fake"`. Replace both walkthrough lines with:

```python
    WALKTHROUGH_LLM: str = "fake"    # provider[:model] — the only LLM switch (plan backend/02)
```

Keep the four key fields as they are. Then grep the whole backend for
`WALKTHROUGH_LLM_PROVIDER` and `WALKTHROUGH_LLM_MODEL` — every hit (code **and**
tests) gets migrated in the steps below; the grep must end at zero hits.

## Step B — providers.py: spec parsing, registry v2, resolve_llm

File: `src/backend/app/agent/llm/providers.py`

First delete the stale shadow directory:

```bash
rm -r src/backend/app/agent/llm/providers/
```

Then rework the module per backend/02:

1. `ProviderSpec` gains `models: tuple[str, ...] = ()` (display list for the future
   picker — **not** a whitelist; do not validate model names against it anywhere).
2. `PROVIDERS` — copy the registry from backend/02 (vercel gets
   `models=("zai/glm-4.7", "moonshotai/kimi-k2.5")`, openai gets
   `models=("gpt-4o-mini",)`).
3. Add the parser — split on the **first** colon only (model ids can contain
   colons and slashes):

```python
def parse_llm_spec(value: str) -> tuple[str, str | None]:
    """'vercel:zai/glm-4.7' -> ('vercel', 'zai/glm-4.7'); 'fake' -> ('fake', None)."""
    provider, _, model = value.strip().partition(":")
    return provider, (model or None)
```

4. Add `ResolvedLLM` + `resolve_llm(override=None, settings=None)` exactly as
   backend/02 shows: resolution order is `override` → spec-string model →
   `default_model`; unknown provider or empty provider name raises `ValueError`
   with the offending string in the message.
5. Rewrite `resolve_model_id()` as a thin wrapper `resolve_llm().model_id` and keep
   it exported (service.py imports it), or migrate service.py to `resolve_llm` —
   pick ONE and leave no duplicate path.
6. Add the (empty) quirks seam at module bottom, verbatim from backend/02:

```python
MODEL_OVERRIDES: dict[str, dict] = {}

def overrides_for(model: str) -> dict:
    for prefix, extra in MODEL_OVERRIDES.items():
        if model.startswith(prefix):
            return extra
    return {}
```

## Step C — structured.py: real ChatOpenAI behind make_chat

File: `src/backend/app/agent/llm/structured.py`

Replace `make_llm` with the backend/02 factory. Requirements:

- `fake` → `FakeLLM(call_type=call_type)` exactly as today.
- everything else → `ChatOpenAI(model=..., base_url=..., api_key=..., **CALL_PARAMS[call_type], **overrides_for(model), timeout=60, max_retries=1)`
  wrapped so `invoke_structured(schema, system, user)` keeps its current signature:
  `.with_structured_output(schema, method="json_mode", include_raw=True)` and a
  two-message input (`SystemMessage`, `HumanMessage`).
- `include_raw=True` is what makes the finish-reason check possible: inspect
  `raw.response_metadata.get("finish_reason")`; if it is `"length"`, raise
  `ValueError("response cut by max_tokens")` so the normal retry path treats it as
  a failed attempt — **a truncated intro or block text must never parse-and-pass**
  (backend/02 rule; this resolves fix 14's `TODO(finish_reason)`).
- `custom` provider: `base_url` comes from `settings.CUSTOM_LLM_BASE_URL`; missing →
  raise at construction with a message naming the setting.
- Key lookup: `getattr(settings, spec.api_key_field)`; missing for a non-fake
  provider → raise at construction naming the field (boot validation in Step E
  catches this before any user does).

`CALL_PARAMS` stays the single table (fix 14 already set 700/1200/800 with the
runaway-guard comment — verify, don't re-apply).

## Step D — service.py: single resolution path

File: `src/backend/app/walkthrough/service.py`

- The preflight `make_llm("intro")` inside `_stream_run` stays — it is exactly the
  fail-fast for "provider misconfigured" at request time.
- `model_id=resolve_model_id()` — migrate to whichever single path Step B kept.

## Step E — boot validation + /models endpoint

1. Find where the FastAPI app starts (search `src/backend/app` for `FastAPI(` and
   for an existing `lifespan` or `@app.on_event("startup")` hook; use what exists).
   Call a new `validate_llm_settings()` (in `providers.py`) that runs
   `resolve_llm()` and, for non-fake providers, checks the key field and — for
   `custom` — `CUSTOM_LLM_BASE_URL`. Malformed spec / unknown provider / missing
   key must **fail the boot** with a message that names the bad value and the
   fix ("set AI_GATEWAY_API_KEY or change WALKTHROUGH_LLM").
2. File: `src/backend/app/walkthrough/routes.py` — add `GET /models` returning the
   backend/02 shape: `active` = `resolve_llm().model_id`; one entry per registry
   provider with `name`, `configured` (bool: key field set, or `True` for keyless),
   `default_model`, `models`; **`fake` listed only when it is active; key values
   never appear**. No UI work now — the endpoint is the future picker's contract.

## Step F — tests

Dir: `src/backend/tests/unit/walkthrough/` (create `test_providers.py`; migrate any
existing test reading the old settings names):

- `parse_llm_spec`: `"fake"` → (`"fake"`, None); `"vercel:zai/glm-4.7"` →
  (`"vercel"`, `"zai/glm-4.7"`); `"custom:llama3:8b"` → model keeps its colon.
- `resolve_llm` order: override beats spec model beats default; unknown provider
  raises with the name in the message.
- `resolve_llm(override=...)` — the picker seam works today even though nothing
  sends it.
- `validate_llm_settings`: fake passes keyless; vercel without `AI_GATEWAY_API_KEY`
  fails naming the field; malformed spec fails.
- `/models` route: no key values in the JSON; `fake` hidden when a real provider is
  active.

## Prove it

```bash
cd src/backend && uv run pytest tests/unit/walkthrough -q
```

Then the switching demo — the entire point of this fix, one env var each time:

```bash
# 1. default: runs keyless
uv run python -m app.walkthrough.cli <project_id> <node_id> 1 | head -3

# 2. unknown provider: must fail AT BOOT with a helpful message
WALKTHROUGH_LLM=nope uv run python -m app.walkthrough.cli <project_id> <node_id> 1

# 3. real provider without key: must fail at boot naming the missing field
WALKTHROUGH_LLM=vercel uv run python -m app.walkthrough.cli <project_id> <node_id> 1

# 4. real provider with key (when you have one): frames stream, and the hello
#    frame's session says "model_id": "vercel:zai/glm-4.7"
WALKTHROUGH_LLM=vercel AI_GATEWAY_API_KEY=... uv run python -m app.walkthrough.cli <project_id> <node_id> 1
```

Grep check: `WALKTHROUGH_LLM_PROVIDER` and `WALKTHROUGH_LLM_MODEL` → zero hits in
`src/backend`.

Anything suspicious that this doc did not tell you to change → README parking lot.
