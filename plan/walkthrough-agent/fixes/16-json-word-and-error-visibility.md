# 16 — JSON-word 400 fix + error visibility (PROMPT_VERSION "3")

> Root cause of the 2026-07-11 all-degraded run (every stop `degraded: true`,
> intros = node descriptions, block texts = focus labels): **OpenAI's `json_object`
> response format rejects any request whose messages do not contain the literal word
> "json"** — and no prompt contained it. Reproduced live:
>
> ```
> BadRequestError: Error code: 400 - "'messages' must contain the word 'json'
> in some form, to use 'response_format' of type 'json_object'."
> ```
>
> Every call 400'd before generating a token, the retry 400'd identically, and the
> pipeline shipped deterministic fallbacks for the whole tour. The second defect this
> fix covers is **why nobody could see that**: `error_log` is collected in the
> pipeline but never streamed, never persisted, and never logged — the frames carry
> only `degraded: true`.
>
> Plan docs already updated (07 Part 1 + Part 2 OUTPUT lines, backend/02 §structured);
> 07 is canonical — copy from it, don't re-word.

Follow the README ground rules: open every file before editing, find code by
searching for the quoted snippet, one step at a time, verify by running.

## Step A — prompts: the OUTPUT lines say "JSON"

File: `src/backend/app/walkthrough/prompts.py`

Replace the closing line of each of the four system prompt constants with the new
07 Part 2 text — exact strings:

| Constant | Old (find) | New (copy from 07) |
|---|---|---|
| `INTRO_FULL_SYSTEM` | `You return: reasoning (1-2 sentences,` … | `You return one JSON object: reasoning (1-2 sentences, your private read of the\nnode — not shown to the user), then intro (the popup text).` |
| `INTRO_CONTEXTUAL_SYSTEM` | `You return: reasoning (private), then intro` … | `You return one JSON object: reasoning (private), then intro (the popup text).` |
| `BLOCK_PLAN_SYSTEM` | `You return, in order: reasoning, block_count, blocks` … | `You return one JSON object, keys in order: reasoning, block_count, blocks\n(each block with start_line, end_line, focus, description).` |
| `BLOCK_TEXT_SYSTEM` | `You return: text (the popup body).` | `You return one JSON object with a single key: text (the popup body).` |

File: `src/backend/app/walkthrough/schemas.py` — find `PROMPT_VERSION = "2"`, bump
to `"3"`. (`SCHEMA_VERSION` stays `"2"` — no shape changed.)

Test (in `tests/unit/walkthrough/test_prompts.py`, alongside the glossary check):
every one of the four rendered system prompts contains the substring `"JSON"`. This
is the regression guard for a failure mode that silently degrades the entire product
while every test stays green.

## Step B — error visibility: stream, and log, every failure

The rule: a degraded stop must be explainable from (1) the server log and (2) the
frame stream, without adding print statements.

1. File: `src/backend/app/agent/llm/structured.py` — in `structured_call`, the
   `except Exception as exc:` branch currently only appends to `error_log`. Add one
   loguru line per failed attempt (backend/02 item 4 promised this and it was never
   implemented):

```python
            logger.warning(
                "walkthrough llm failure call_type={} attempt={} error={}",
                call_type, attempt + 1, exc,
            )
```

   Also log validation-issue retries the same way (`issues` branch). Import
   `from loguru import logger`.

2. File: `src/backend/app/walkthrough/patcher.py` — add one typed helper next to
   `set_status`:

```python
    async def append_error(self, message: str) -> None:
        await self._frame(
            [{"op": "add", "path": "/error_log/-", "value": message}],
        )
```

3. File: `src/backend/app/walkthrough/pipeline.py` — everywhere the pipeline does
   `error_log.extend(...)` with a non-empty list, also
   `await patcher.append_error(msg)` for each message (a tiny
   `async def _record(errors)` helper keeps it one line per site). The mirror then
   carries `error_log`, so the frontend and the CLI `--frames` dump both show *why*
   a stop degraded — no frontend change needed (the generic patch reducer already
   applies any path).

## Step C — block text: "names in this block" must be range-filtered

Found while diagnosing (06 contract violation, prompt-quality not correctness):
`block_text_user_prompt` passes **all** `ctx.child_lines` as `### names in this
block`, so every block sees every child name — off-range names invite off-topic
mentions rule 4 then has to fight.

- File: `src/backend/app/walkthrough/context.py` — keep, per child line, the line
  number it starts at (extend the entries to `(line_no | None, rendered_line)` in a
  new field, e.g. `child_line_entries`; `child_lines` stays the rendered list for
  the intro).
- File: `src/backend/app/walkthrough/prompts.py` (or the pipeline where the
  block-text context is copied) — the block-text call renders only entries whose
  `line_no` falls inside `[block_start, block_end]`; none → omit the section.

## Prove it

```bash
cd src/backend && uv run pytest tests/unit/walkthrough -q
```

Then the live check that failed before (uses the configured real provider — one
tiny call):

```bash
cd src/backend && uv run python - <<'EOF'
import asyncio
from app.agent.llm.structured import structured_call
from app.walkthrough.schemas import IntroOut
from app.walkthrough.prompts import PERSONA, GLOSSARY

async def main():
    result, errors = await structured_call(
        "intro", IntroOut,
        PERSONA + "\n\n" + GLOSSARY +
        "\n\nYou return one JSON object: reasoning, then intro.",
        "### node\nfunction charge\n\nIntroduce this node now.",
    )
    print("errors:", errors)
    print("result:", result)

asyncio.run(main())
EOF
```

`errors` must be `[]` and `result` a real `IntroOut` — not `None`.

Finally rerun the full stream (same command as before) and check the frames:

- intros and block texts are real sentences, `degraded: false`;
- if anything still degrades, the stream itself now contains `error_log` add-ops
  saying exactly why.

Anything suspicious that this doc did not tell you to change → README parking lot.
