# API 01 — Endpoints and Layering

The HTTP surface, in the house pattern. The MVP's walkthrough kept its routes
inside `app/walkthrough/` — v2 explicitly returns to the standard layout: **routes
in `app/api/v1/`, registered in `app/api/root.py`, DI through
`app/api/dependencies.py`, logic in a service, persistence in a repo.** Separate
per-feature route folders are the thing we are *not* doing.

## Routes

```python
# app/api/v1/conversation_routes.py
router = APIRouter()

def get_agent_service(uow: ProjectUoW = Depends(get_project_uow)) -> AgentService:
    return AgentService(uow)
```

registered in `app/api/root.py`:

```python
router.include_router(conversation_routes.router,
                      prefix="/conversations", tags=["conversations"])
```

| Method + path | Body / params | Returns | Notes |
|---|---|---|---|
| `POST /conversations` | `project_id` (query, via `get_project_uow` like every route) | conversation snapshot | creates `idle`, empty |
| `GET /conversations` | `project_id` | summaries (id, title, updated_at, status) | reload/library path |
| `GET /conversations/{id}` | | persisted snapshot | the frontend re-opens mirrors from this |
| `POST /conversations/{id}/messages` | `{parts: [text \| node_ref…], options?: {effort}}` | **NDJSON stream** (harness/02) | 409 if a run is active — same guard style as the walkthrough service; `effort` overrides the reasoning default for this run (harness/04) |
| `POST /conversations/{id}/decision` | `{tool_call_id, decision, overrides?}` | 204 | resumes the interrupted run; frames keep flowing on the open message stream |
| `POST /conversations/{id}/cancel` | | 204 | cooperative cancel of the active run |
| `GET /conversations/{id}/artifacts/{doc}` | | artifact snapshot | mounting a renderer after reload |

**Why decision/cancel are separate POSTs and not stream messages.** The message
stream is a *response* (server → client); NDJSON responses are one-directional.
Small control POSTs against the run are the simplest thing that works, mirror how
`/walkthroughs/run` + abort behave today, and leave the stream protocol purely
about documents.

**Why the UoW dependency chain is reused untouched.** `get_project_uow` already
resolves the project, honors `X-Vnoc-Branch`, and carries ref pinning. Conversations
run at head; each task tool pins its own commit at start (tools/01) — both behaviors
fall out of passing the right `Repositories` from the same UoW.

## Layering (one request, top to bottom)

```
conversation_routes.py          HTTP shapes, status codes, DI — nothing else
  └─ AgentService               app/agent/service.py
       run lifecycle: start / resume(Command) / cancel; one active run per
       conversation; owns the queue between the agent loop and the NDJSON
       response (the walkthrough service's producer/queue pattern, reused)
       └─ harness/loop.py       create_agent invocation (harness/01)
            ├─ middleware       enrichment · estimate/confirm · limits
            ├─ stream_adapter   events → patcher helpers (harness/02)
            └─ tools/*          walkthrough tool → app/walkthrough/service.py
       └─ patcher v2            mirrors → frames + persistence triggers
            └─ ConversationRepo / WalkthroughSessionRepo   (data-model/02)
                 └─ TerminusDB (project DB)
```

Schemas split follows the house style: wire/request/response models next to the
routes' domain (`app/agent/schemas/`), document schema classes in
`app/db/schema/`.

## Errors, honestly

| Case | Behavior |
|---|---|
| LLM provider not configured | first frame is a conversation-doc `close` with `status: "error"` and a human message — the fail-at-first-frame pattern the walkthrough uses today |
| tool failure | never an HTTP error — it is a tool part in `error` state; the turn continues (harness/01) |
| fatal mid-run (DB down, model unreachable) | assistant message finalized with `stop_reason: "error"` + metadata.error; conversation status `error`; stream closes with `status: "error"` |
| decision for an unknown/settled tool_call_id | 409 with the current tool state — the client resyncs from `GET /conversations/{id}` |

## Settings

```
AGENT_LLM            same spec format as WALKTHROUGH_LLM ("vercel:zai/glm-4.7"),
                     resolved through the existing providers module; falls back to
                     WALKTHROUGH_LLM so one configured provider runs everything
AGENT_MAX_STEPS      per-turn model-call cap (default 12)
AGENT_REASONING_EFFORT  off | low | medium | high (default medium) — mapped to
                     each provider's reasoning params by the capability
                     registry (harness/04); per-message override wins
AGENT_AUTO_RUN_LIMIT confirmation threshold in estimated LLM calls (default 15)
PROMPT_OVERRIDE_DIR  optional, dev only (prompts/01)
```

**Why a separate `AGENT_LLM`.** The orchestrator can justify a stronger model than
the per-stop micro-calls (which keep the small-model contract). Per-call-type
overrides already exist in spirit via `CALL_PARAMS` / `MODEL_OVERRIDES` in
`app/agent/llm/` — this is one more key, not a new mechanism.
