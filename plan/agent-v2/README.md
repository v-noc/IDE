# Agent v2 — Chat Agent Harness (Vision + Backend Plan)

The walkthrough MVP was a launcher: pick a node, pick a depth, press run. v2 turns
it into a **chat agent** in the style of Claude Code / Cursor: the user talks
normally, attaches a node from the canvas, and one agent decides what to do — answer
directly, or run a tool. The walkthrough pipeline survives **unchanged** as the
first tool.

This plan covers the vision, the backend, and the frontend (`frontend/` — added
after the backend docs). The wire protocol (harness/02) is the contract between
the two halves. `frontendv2/` (added after F1–F4 shipped) is the visual redesign
of the agent panel: the Claude-design mock made real in a clean `AgentV2/`
feature folder — data layer moved, presentation rebuilt, all four tools visible
but only walkthrough enabled.

## The user flow (the whole product in one story)

1. The user opens the chat panel and drags a node onto the composer (or just types).
2. The backend always injects the **project name + description** into the system
   prompt, and expands each attached node into a rich context block (parent,
   siblings, children, docs, code) — before the model sees anything.
3. The agent reads the message and **thinks about intent** — if the model has a
   native reasoning channel it shows up as a collapsible thinking row (sized by
   the effort setting); either way, one short status sentence precedes any tool
   call.
   - Plain question → it answers directly from the enriched context. No tools.
   - Walkthrough ask → it distills the user's goal ("quick summary of how retries
     work") and calls the `walkthrough` tool with that intent, a verbosity hint,
     and a suggested depth guessed from the prompt.
4. The harness computes the **estimate** (nodes, LLM calls) and the subtree's
   **real max depth** (WOQL query, hard cap 5), then pauses the run and shows a
   confirmation card: estimate + a depth knob prefilled with the suggestion,
   capped at the real max.
5. The user adjusts the depth if they want, confirms (or cancels), and the tour
   streams — narration angled by their intent, verbose or quick as asked.
6. The agent closes with a one-line outcome. The conversation, the artifact, and
   every token spent are persisted.

Search/query tools are **deliberately out of scope for this build** — the attached
node is the only way the agent gets a node id. That keeps the first build small and
makes "fabricated node ids" impossible by construction. Search is a named seam
(tools/01), not a redesign.

## Dendrogram — the system, top-down

Read this tree from the root down; each branch is a plan folder, each leaf is a
decision explained in the docs.

```
agent v2
│
├── harness/ ──────────────── the conversation engine (one agent, one loop)
│   ├── 01 agent loop         LangGraph `create_agent`: model ↔ tools cycle
│   │   ├── middleware        project header · node enrichment · estimate/confirm · step limits
│   │   ├── history           parts → model messages, deterministic, in code
│   │   └── checkpointer      in-memory, thread_id = conversation_id (resume for interrupts)
│   ├── 02 streaming          multi-doc NDJSON patches: open / patch / close (+ `append` op)
│   │   ├── stream adapter    LangGraph events → typed patches (one file knows the framework)
│   │   └── patcher v2        the walkthrough Patcher, generalized to many documents
│   ├── 03 confirmation       estimate → interrupt() → decision endpoint
│   │   ├── depth knob        agent suggests, user decides, backend clamps
│   │   └── max depth         WOQL bounded-path probe, hard cap 5, per-subtree real cap
│   └── 04 reasoning          native CoT surfaced (extracted or summarized), never forced
│       ├── effort knob       off/low/medium/high → per-provider params (capability registry)
│       └── status line       one plain sentence before each tool call — text, not thinking
│
├── data-model/ ───────────── what a conversation IS
│   ├── 01 parts              Message = list of typed parts (OpenCode-shaped)
│   │   ├── metadata          model id, token usage, cost, timing → one metadata field
│   │   └── tool state        pending → awaiting_confirmation → running → completed/error
│   └── 02 persistence        ConversationRepo in the existing BaseRepo/Repositories pattern
│
├── context-engineering/ ──── what the model sees, and nothing else
│   ├── 01 principles         assembled not searched · caps by construction · XML tags
│   ├── 02 context factory    ONE builder: choose parent depth / children depth / what to
│   │                         include (description, docs, code) — every consumer uses it
│   └── 03 turn enrichment    project header (always) · attached-node blocks · intent distillation
│
├── tools/ ────────────────── what the agent can DO
│   ├── 01 registry           ToolSpec → LangChain tools; adding a tool = one spec + one module
│   └── 02 walkthrough tool   thin wrapper over app/walkthrough; user_query + verbosity + depth
│
├── prompts/ ──────────────── every model-facing string, versioned and replaceable
│   └── 01 prompt registry    named + versioned prompts, layered assembly, file overrides
│
├── api/ ──────────────────── the HTTP surface, in the existing house pattern
│   └── 01 endpoints          app/api/v1/conversation_routes.py · service · DI · NDJSON stream
│
├── frontend/ ─────────────── the chat surface (existing Agent feature, made real)
│   ├── 01 overview           what survives (chrome, player), what's replaced (fixtures), F-phases
│   ├── 02 mirror store       docId → mirror; `append` pre-pass; rAF-coalesced stream; reload
│   ├── 03 thread & parts     part-registry rendering · markdown streaming · auto-scroll rules
│   ├── 04 thinking UI        Cursor-style: live clamped tail → "Thought for 3s" collapse
│   ├── 05 composer           node chips from canvas selection · quick actions · effort knob · send/stop
│   ├── 06 tool & confirm UI  five-faced tool card · depth slider with real max · live re-estimate
│   └── 07 artifacts          render-hint registry · bridge that mounts the existing player
│
└── frontendv2/ ───────────── the redesign (design/agent-panel.dc.html made real)
    ├── 01 structure          AgentV2 feature folder · React conventions · design tokens
    ├── 02 panel & thread     chrome, header, messages, auto-scroll
    ├── 03 tool cards         one shell, six states, per-tool faces behind a registry
    ├── 04 composer & picker  tool registry · coming-soon gating · toolHint semantics
    ├── 05 canvas playback    step card, bottom pill, node glow — executor untouched
    └── 06 build order        V0–V4 phases · dev switch · v1 retirement checklist
```

## Design stance (carried from the MVP, one level up)

| Principle | In v2 |
|---|---|
| Deterministic first | The agent **routes**; tools author content. The agent never writes tour text, descriptions, or docs itself. |
| Frontend never interprets LLM output | Everything on the wire is a typed part or a typed patch. |
| Estimate before spend | Every task tool must implement `estimate()`; the harness owns the confirm gate. |
| Failure is boring | A failed tool never kills a turn; the agent is told what failed and answers anyway. |
| Incremental persistence | Conversations persist per part, artifacts per item. A crash leaves a truthful partial record. |
| Don't hand-roll what the framework gives | LangChain/LangGraph own the loop, interrupts, and checkpointing. We own the parts model, the patcher, and the wire. |

## What exists today (and its fate)

| Existing code | Fate |
|---|---|
| `app/walkthrough/` (pipeline, traversal, context, prompts, patcher, service) | **Pipeline untouched.** Wrapped by the `walkthrough` tool. Its `context.py` formats migrate to the context factory over time; its `patcher.py` is the template for patcher v2. |
| `app/walkthrough/routes.py` (`/walkthroughs/*`) | Kept until the frontend moves to conversations, then deprecated. New code follows the house API pattern instead (routes under `app/api/v1/`). |
| `app/agent/llm/` (providers, structured, fake) | **Reused as-is.** The agent loop builds its chat model through `resolve_llm`; tools keep `structured_call`. |
| `app/agent/{chat,context,runner,...}` stale `__pycache__` dirs | Leftovers from an old experiment — delete the empty dirs when implementation starts. |
| `plan/walkthrough-agent/` | Superseded by this plan (removed). |

## Target backend layout

Following the existing folder conventions — agent logic in `app/agent/`, routes in
`app/api/v1/`, repository in `app/core/repository/`:

```
src/backend/app/agent/
├── llm/                      (exists, unchanged)
├── schemas/
│   ├── conversation.py       Conversation · Message · Part union · MessageMetadata
│   └── wire.py               NDJSON frame shapes
├── harness/
│   ├── loop.py               create_agent assembly
│   ├── middleware.py         ProjectContext · NodeEnrichment · EstimateConfirm · Limits
│   ├── stream_adapter.py     LangGraph events → patches
│   ├── history.py            parts → model messages
│   └── patcher.py            multi-doc mirrors + typed helpers
├── context/
│   ├── factory.py            ContextFactory + ContextSpec + presets
│   └── xml.py                tag rendering
├── prompts/
│   ├── registry.py           PromptDef + PromptRegistry
│   └── agent.py              orchestrator system prompt (versioned)
├── tools/
│   ├── base.py               ToolSpec · TaskTool protocol · registry
│   └── walkthrough_tool.py   wrapper over app/walkthrough
└── service.py                AgentService: start / resume / cancel a run

src/backend/app/core/repository/conversation_repo.py   (registered in Repositories)
src/backend/app/api/v1/conversation_routes.py          (registered in api/root.py)
src/backend/app/db/schema/…                            Conversation/Message doc types
```

## Build order

Each phase ends runnable; later phases only add.

| Phase | Contents | Demo gate |
|---|---|---|
| **1 — Skeleton** | schemas + ConversationRepo + routes + patcher v2 + a fake-LLM echo loop | Create a conversation, send a message, watch text parts stream and persist. No real model needed (`fake` provider). |
| **2 — Real agent, zero tools** | `create_agent` loop + project header + attached-node enrichment (context factory presets) + history builder | Drop a node, ask "what does this do?" — the agent answers from the enriched block, streaming; on a reasoning model the thinking row streams too (harness/04). |
| **3 — Walkthrough as a tool** | tool registry + walkthrough wrapper + estimate/confirm interrupt + WOQL max-depth + decision endpoint | "Walk me through how X works" → confirm card (prefilled depth, real max) → tour streams as an artifact doc. |
| **4 — Polish** | title generation, cancellation, degraded reporting, usage/cost in metadata, prompt-version stamps, eval fixtures | A 10-turn conversation reloads faithfully; every message shows model + tokens. |

Phase 1+2 are the honest foundation gate: if parts stream, persist, and enrich with
zero tools, every later tool is a registry entry.
