# Data Model 02 — Persistence (the existing repository pattern)

Conversations and artifacts are TerminusDB documents, read and written through the
house repository pattern — `BaseRepo` subclasses registered in the `Repositories`
container. No new persistence style; that is the point.

## Decision: a `ConversationRepo` in `app/core/repository/`, like every other repo

```
app/core/repository/conversation_repo.py

class ConversationRepo(BaseRepo[ConversationNode, ConversationSchema]):
    async def get_conversation(self, conversation_id) -> Conversation | None
    async def list_for_project(self, limit, offset) -> list[ConversationSummary]
    async def create_conversation(self, conversation) -> ...
    async def append_message(self, conversation_id, message) -> ...
    async def update_message(self, conversation_id, message) -> ...   # finalize: parts + metadata
    async def set_status(self, conversation_id, status) -> ...
```

Registered in the `Repositories` container (`app/core/repository/__init__.py`)
next to `document_repo`, `log_repo`, etc., and reached through `ProjectUoW` exactly
like everything else.

**Why the house pattern and not a self-contained module.** The MVP's walkthrough
kept everything inside `app/walkthrough/` including its routes — convenient for a
spike, but it created a second way of doing things: its own route registration
style, its own service wiring, no repo layer (sessions were never persisted at
all). v2's rule: agent *logic* lives in `app/agent/`, but persistence goes through
`core/repository` and HTTP goes through `api/v1` (api/01), because that is where
every existing convention — UoW pinning, branch headers, schema registration,
`Repositories` DI — already works and is already tested.

## Where documents live

| Document | DB | Why |
|---|---|---|
| `Conversation` (with embedded messages/parts) | the **project DB** | conversations are about one project's graph; the project DB is what `ProjectUoW` already scopes to, and deleting a project takes its conversations with it |
| `WalkthroughSession` and future artifacts | the project DB, own doc types | artifacts are per-project too; each records its own `branch` + `commit_id` (pinning is per **task**, not per conversation — a conversation outlives commits) |

Schema classes are added in `app/db/schema/` alongside the existing document
types, with `schema_version` fields as plain strings.

**Embedded messages vs separate message docs — start embedded.** One conversation
= one document, updated by replacing (TerminusDB `update_document`). Simple,
matches the mirror (the patcher's in-memory conversation *is* the stored shape),
and read-back is one `get_document`. The seam if conversations grow huge: split
messages into child documents keyed by conversation id — `ConversationRepo` is the
only module that would change, which is exactly why persistence hides behind a
repo.

## When writes happen (incremental persistence)

The rule from the MVP, kept: **a crash leaves a truthful partial record.**

| Moment | Write |
|---|---|
| user message received | `append_message` (user parts, verbatim) |
| assistant message opened | `append_message` (empty parts skeleton) |
| each part completes (reasoning settled, tool state settles, text finalized) | `update_message` with the patcher's mirror |
| run ends / interrupts / errors | `update_message` (metadata: usage, stop_reason) + `set_status` |
| artifact items | the **tool** persists its own artifact per item, exactly as the walkthrough does per `node_done` today |

**Why per-part, not per-token.** Token-level writes would hammer the DB for no
recovery value — losing the tail of one streaming sentence is a shrug; losing a
completed tool call is a lie in the transcript. Per-part is the honest granularity,
and the mirror makes it free (the patcher already holds the exact object to
persist).

**Why the mirror is the thing we persist.** Same guarantee as the walkthrough
patcher: the object described by the streamed patches and the object written to
TerminusDB are one object. Stored and streamed state cannot diverge, so a reload
(`GET /conversations/{id}`) always reconstructs what the client saw.

## Read paths

- `GET /conversations/{id}` → the persisted snapshot; the frontend re-opens
  mirrors from it (`open` frame equivalent) — this is the reload path.
- `GET /conversations?project_id=…` → summaries (id, title, updated_at, status)
  for a later conversation library; the repo method exists from day one because
  listing is trivial, the UI for it is Phase-later.
- Artifacts load by their own doc id when a renderer mounts one
  (`ArtifactRef.doc`), through their own repo (`WalkthroughSessionRepo`).

## What is deliberately not persisted

| Not stored | Why |
|---|---|
| LangGraph checkpoints | resume mechanics only (harness/01); the conversation doc is the durable truth |
| raw LangGraph event streams | the adapter's output (parts) is the record; events are framework-shaped noise |
| model prompts as sent | recoverable = history.py(stored parts) + prompt registry at the stamped version; store *versions*, not copies. LangSmith traces cover debugging. |
