# 00 — Scope

What the backend MVP builds, what it reuses, and what it skips. Checked against the
code, not assumed.

## What already exists (reuse, don't rebuild)

| Existing thing | Where | Used for |
|---|---|---|
| Settings pattern | `app/config/settings.py` (pydantic-settings, `get_settings()` cached) | Provider + model config lives here |
| Route pattern | `app/api/v1/*_routes.py`, `APIRouter` per domain; packages with `routes/` + `schemas/` for bigger domains (see `conversations/`) | `walkthrough_routes.py` follows it |
| Service / repository layers | `app/core/services/`, `app/core/repository/` (subpackages per domain) | Traversal + context fetch through these |
| Code by node | `GET /read-code/` (`code_routes.py`) → code element service | `numbered_code` for prompts |
| Subtree / children (incl. lazy + paginated) | `GET /descendants` + structure repos | The traversal walk |
| Lineage by node id | `GET /lineage` → `path_ids` | Estimate-time validation; shares logic with frontend injection |
| TerminusDB client + doc schemas | `app/db/terminus_client/`, `app/db/schema/` | Session persistence + commit id |
| Empty agent scaffolding | `app/agent/{llm,chat,workflows,...}` (folders exist, **no code**) | Provider layer takes its reserved seat in `agent/llm/` |
| Logging | loguru | Pipeline + retry/fallback logs |
| Fast JSON | orjson | NDJSON frame serialization |

## New dependencies (the complete list)

```toml
# pyproject.toml [project.dependencies]
"langchain>=0.3",          # prompts, with_structured_output
"langchain-openai>=0.3",   # ChatOpenAI — covers every OpenAI-compatible endpoint
"langgraph>=0.4",          # the pipeline graph (parent 05)
"jsonpatch>=1.33",         # RFC 6902 ops for the patcher (parent 04)
```

Deliberately **not** added: provider-specific SDKs (`openai` comes transitively via
`langchain-openai`; no `anthropic`, no `google-genai` — see 02), no `fast-json-patch`
equivalent beyond `jsonpatch`, no vector/embedding libraries.

## What MVP builds

1. **Provider layer** (`app/agent/llm/`): registry (openai / vercel / custom / fake),
   settings, `make_chat(call_type)`, structured-output helper with the
   retry-once-then-fallback contract (02).
2. **Walkthrough feature** (`app/walkthrough/`): traversal, context builders, prompts,
   LangGraph pipeline, patcher, schemas, fallbacks — implementing parent 03–07.
3. **Two endpoints**: `GET /api/v1/walkthroughs/estimate`, `POST
   /api/v1/walkthroughs/run` (NDJSON patch stream), plus `GET
   /api/v1/walkthroughs/{id}` for replay (03).
4. **Persistence**: `WalkthroughSessionSchema` TerminusDB doc type, commit pinned at
   run start, written incrementally (04).
5. **CLI harness + tests** running on the `fake` provider (05).

## What MVP skips (and why it's safe)

| Skipped | Why safe |
|---|---|
| Provider selection UI / per-request model override | `make_chat` takes the value from settings today; a request field can shadow it later without signature changes |
| Non-OpenAI-compatible SDKs (Anthropic, Gemini) | The registry maps a name → base URL + key; a genuinely new SDK is a new `make_chat` branch, isolated in one file |
| Streaming tokens (string-append frames) | Texts are whole structured outputs (parent 04); the patcher contract already documents the upgrade |
| Resume from `seq` | Frames are numbered and the session is persisted incrementally; resume is a read path added later |
| Rate limiting / queuing of runs | Single-user IDE; one run at a time enforced per project id with a simple in-process lock |
| Evals beyond the fixture re-run script | Parent 07's checks; a real eval rig waits for real usage |

## The one behavioral contract

> `POST /run` always terminates the stream with an `end` frame, always leaves a
> truthful session document in TerminusDB (`generating` → `complete` / `error` /
> `aborted`), and never lets one bad LLM call kill a tour — degraded steps are marked,
> never missing.

Everything in 03 and 05 serves that sentence.
