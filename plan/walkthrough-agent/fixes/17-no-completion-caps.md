# 17 — Remove completion caps; length is a prompt target (PROMPT_VERSION "4")

> Root cause of the second failing run (2026-07-11, `WALKTHROUGH_LLM=openai:gpt-5-mini`),
> visible in the streamed `error_log` thanks to fix 16:
>
> ```
> intro attempt 1: Could not parse response content as the length limit was
> reached - CompletionUsage(completion_tokens=700, ..., reasoning_tokens=700, ...)
> ```
>
> `gpt-5-mini` is a reasoning model: `max_tokens` counts its **hidden reasoning**
> too, and the reasoning runs first. Our intro cap of 700 was consumed entirely by
> thinking (`reasoning_tokens=700`), zero tokens were left for content, both
> attempts "failed", and the stop shipped degraded. The rule going forward (owner's
> call, recorded in 07/backend-02/05/08): **machinery never limits or breaks a
> response for length — no `max_tokens` anywhere; sentence counts are suggestions
> in the prompt ("Aim for 2-4 sentences"), not enforcement.** Cost control stays
> where it belongs: the tour-level estimate + visit cap (03).

Follow the README ground rules: open every file before editing, find code by
searching for the quoted snippet, one step at a time, verify by running.

## Step A — structured.py: drop the caps and the finish_reason police

File: `src/backend/app/agent/llm/structured.py`

1. Find the `CALL_PARAMS` dict. Replace it (comment included — it documents a
   decision people will be tempted to reverse):

```python
# NO completion caps — deliberate (learned live, 2026-07-11). Reasoning models
# (gpt-5 family, o-series, GLM/Kimi thinking modes) spend max_tokens on hidden
# reasoning FIRST: observed reasoning_tokens=700 of a 700 cap, zero content,
# every intro failing "length limit reached". Length is steered by the prompts
# ("aim for 2-4 sentences" — a target, not a limit); cost is controlled by the
# tour-level estimate + visit cap, never by cutting a generation mid-thought.
CALL_PARAMS = {
    "intro": {"temperature": 0.5},
    "block_plan": {"temperature": 0.2},
    "block_text": {"temperature": 0.5},
}
```

2. In `ChatOpenAILLM.invoke_structured`, find and **delete** the finish_reason
   block:

```python
        finish_reason = None
        if raw is not None:
            meta = getattr(raw, "response_metadata", None) or {}
            finish_reason = meta.get("finish_reason")

        if finish_reason == "length":
            raise ValueError("response cut by max_tokens")
```

   Keep `include_raw=True` and the `parsing_error` / `parsed is None` handling —
   those are real failures. If a provider's *own* hard limit ever truncates a
   response, the JSON fails to parse and lands in the existing retry → fallback
   path; no special case.

## Step B — prompts: sentence counts become targets

File: `src/backend/app/walkthrough/prompts.py` — copy the exact new wording from
07 Part 2 (canonical):

| Constant | Old (find) | New |
|---|---|---|
| `INTRO_FULL_SYSTEM` rule 1 | `1. 2-4 sentences. First sentence:` | `1. Aim for 2-4 sentences. First sentence:` |
| `INTRO_CONTEXTUAL_SYSTEM` rule 1 | `1. 2-3 sentences, in the caller's context:` | `1. Aim for 2-3 sentences, in the caller's context:` |
| `BLOCK_TEXT_SYSTEM` rule 2 | `2. 2-4 sentences. Explain what the block does` | `2. Aim for 2-4 sentences. Explain what the block does` |

File: `src/backend/app/walkthrough/schemas.py` — find `PROMPT_VERSION = "3"`,
bump to `"4"`. (`SCHEMA_VERSION` stays `"2"` — no shape changed.)

## Step C (optional, cost) — tame gpt-5's hidden reasoning via the overrides seam

The caps are gone, so gpt-5-mini now *succeeds* but pays for its hidden thinking
on every call (~700 reasoning tokens × ~2 calls per stop adds up). The knob for
that is `MODEL_OVERRIDES` in `src/backend/app/agent/llm/providers.py`:

```python
MODEL_OVERRIDES: dict[str, dict] = {
    "gpt-5": {"reasoning_effort": "low"},
}
```

Verify `langchain_openai`'s `ChatOpenAI` in the installed version accepts
`reasoning_effort` as a constructor kwarg (open the installed package or try one
call); if it does not, pass it via `{"extra_body": {"reasoning_effort": "low"}}`
instead. This step is optional — skip it if either form errors, and note it in
the parking lot. Never put it in `CALL_PARAMS` (it is a per-model concern).

## Step D — tests

- Grep `tests/unit/walkthrough` for `max_tokens` and `finish_reason` — update or
  delete any test asserting the old cap values or the length-failure behavior.
- Add one assertion in the CALL_PARAMS test (or create it): **no entry contains
  `max_tokens`** — the regression guard for someone "helpfully" re-adding a cap.

## Prove it

```bash
cd src/backend && uv run pytest tests/unit/walkthrough -q
```

Then rerun the stream (same CLI/frontend run as before) and check:

- no `error_log` op contains "length limit was reached";
- every intro and block text is a complete paragraph, `degraded: false`;
- with Step C applied, compare `usage.completion_tokens` in the final session
  against a run without it — it should drop noticeably.

Anything suspicious that this doc did not tell you to change → README parking lot.
