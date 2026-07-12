# Walkthrough Agent — MVP Plan

> An AI agent that walks the user through code on the V-NOC canvas: the user drops a
> function, class, file, or folder node into the chat, picks a **depth**, and the agent
> plays a guided tour — selecting nodes, opening code, and highlighting line ranges with
> popup explanations in a custom Monaco view.

This plan replaces the legacy `plan/cognitive-replay/` design. Cognitive-replay described
a video-style **playback UI** (timeline, seek bar). This plan describes the **agent that
produces the walkthrough**, plus a simpler click-through playback for MVP.

## How to read this plan

Files go **top-to-bottom, general to specific** (dendrogram style). Read in order.
Each file covers one domain and nothing else.

| # | File | Domain | Question it answers |
|---|------|--------|---------------------|
| 00 | [00-overview.md](00-overview.md) | Product | What are we building? What is in and out of MVP? |
| 01 | [01-user-flow.md](01-user-flow.md) | UX | What does the user see and do, start to finish? |
| 02 | [02-architecture.md](02-architecture.md) | System | The big pieces and how they talk. |
| 03 | [03-traversal.md](03-traversal.md) | Backend logic | How depth turns into a visit list and a step estimate — no LLM. |
| 04 | [04-data-types.md](04-data-types.md) | Contracts | Every type: request, block plan, step, action, event. |
| 05 | [05-orchestration.md](05-orchestration.md) | Agent | The LangGraph pipeline: node loop → intro → block plan → block explanations. |
| 06 | [06-context-engineering.md](06-context-engineering.md) | Agent | What data goes into each LLM call, and what never does. |
| 07 | [07-prompting.md](07-prompting.md) | Agent | The exact prompts, plus a lesson on writing them. |
| 08 | [08-chain-of-thought.md](08-chain-of-thought.md) | Agent | What CoT is, what works on small models, what we use. |
| 09 | [09-frontend-playback.md](09-frontend-playback.md) | Frontend | Monaco highlight component, popup, step executor. |
| 10 | [10-implementation-steps.md](10-implementation-steps.md) | Delivery | Build order, phase by phase. |
| — | [frontend/](frontend/README.md) | Frontend (detailed) | Concrete build plan against the existing React code: folders, wire + mock sources, store, canvas injection, edge cases, build order. Supersedes 09 where they differ. |
| — | [backend/](backend/README.md) | Backend (detailed) | Concrete build plan against the existing FastAPI code: folders, the configurable LLM provider layer (OpenAI / Vercel gateway / custom / fake), routes + patcher + NDJSON transport, persistence, testing, build order. |
| — | [fixes/](fixes/README.md) | Review + fixes | Findings from reviewing the first implementation, as a verify-first fix guide: mock mode on real node data, play-flow/step-card UI, frontend and backend correctness bugs (3 with failing tests), verification checklist. |

## The pipeline in one picture

```
traversal (code, no LLM) ──► visit list + step estimate
        │
        ▼  for each node, in order:
   ┌──────────────────────────────────────────────────────────┐
   │ 1. INTRO        narrator LLM — outside-in description    │
   │                 → emitted immediately as the node step    │
   │ 2. BLOCK PLAN   only if node has code ≥ line gate:        │
   │                 block-planner LLM → plan JSON             │
   │                 { blocks: [{start_line, end_line, …}] }   │
   │                 → validated by code; fallback: even split │
   │ 3. EXPLAIN      one small LLM call per block →            │
   │                 explanation text, nested under the node   │
   └──────────────────────────────────────────────────────────┘
        │
        ▼
steps stream to canvas: select_node → show_code → highlight_lines × blocks
```

Three kinds of LLM call, all structured output, all tiny:

- **Narrator (intro)** — once per visited node. Describes the node from outside using
  its description, docs, and children's names. Never sees children's code.
- **Block planner** — only for code nodes long enough to split (line-count gate).
  Decides how many blocks and which line ranges, with a short reasoning field first.
- **Block explainer** — once per block. Writes one explanation for one line range,
  given the full node code plus one-line summaries of the blocks already explained.

There is **no node-level planner LLM**. Traversal decides which nodes the tour visits
and in what order; every visited node is explained. The only planning the LLM does is
inside a single node's code — and that plan is itself a small JSON artifact we can log,
validate, and eval.

## Design principles (apply everywhere)

1. **Deterministic first.** Code decides *where* the tour goes (traversal by depth),
   *whether* a node's code is split (line-count gate), and *which action plays next*
   (fixed pattern per node kind). The LLM only decides how to split and what to say.
2. **Built for small, cheap models** (GLM 4.7 / Kimi 2.5 class). No one-shotting. Every
   call has one job, one screen of context, a tiny schema, one retry, and a
   deterministic fallback. Thinking happens as a reasoning field **inside** each call
   (see 08), not as a separate planning stage.
3. **One user setting: depth.** Steps are computed, not chosen. Because the pipeline is
   deterministic we show node count, step estimate, and LLM-call cost **before** the
   user clicks Generate.
4. **Three actions only:** `select_node`, `show_code`, `highlight_lines`. The pipeline
   implies the action; the model never picks one.
5. **Small context, on purpose.** Each call sees only the code of the node it works on.
   Children appear as one-line `name — description` entries, never as code.

## Where this differs from Eregna v2 (and why)

| Eregna v2 | Here | Why |
|---|---|---|
| Planner **chooses** page elements (3 LLM calls) | **No node planner.** Traversal fixes the visit list; all visited nodes are explained | The graph already encodes structure and order; choosing was the risky, expensive part |
| Planner guesses `expectedSteps` | Step counts **computed** from line counts | The graph stores `position.line_no` / `end_line_no` |
| Stepper picks among 5 action types | Action pattern **fixed by node kind** | A code node is always select → show → highlight × blocks |
| One stepper call emits a chapter's steps | Block plan and block explanations are **separate calls** | Structure (line numbers) needs precision; prose needs quality; splitting lets each be tiny and independently retried |
| Separate visible CoT stage | CoT lives as a leading field inside each call | With no free choices left, a standalone reasoning stage isn't worth its latency and cost |
