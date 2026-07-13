# Agent v3 — The Write Tools: `describe_nodes` and `document_nodes`

v2 built the chat harness and made the walkthrough its first (read-only) task
tool. v3 adds the first tools that **write into the graph**: a description
generator and a documentation generator. Both run like the walkthrough — pick a
node, choose a depth, see an estimate, confirm, watch a live checklist — but they
walk the tree in the **opposite direction**, and they leave the project
permanently better: every future walkthrough, every enrichment block, every
NodeCard reads what these tools wrote.

This is also the proof of v2's central claim: *adding a tool = a spec + a
module*. If v3 requires harness changes, v2's registry design failed its test.

## The two tools in one sentence each

- **`describe_nodes`** — for a selected node and its children down to a depth,
  write a 2–3 sentence description per node, **children first**, so every parent
  is summarized from its children's fresh summaries.
- **`document_nodes`** — same traversal, same direction, but per node it writes a
  full overview-style document: what it is, why it exists, how to use it, its
  role in the project, and — for containers — how its children work together,
  angled by the user's intent.

## Why children-first (post-order) — the user's instinct, confirmed

The walkthrough reads the tree **pre-order** (outside-in): a reader meets the
parent before its parts. An *author* works the other way: you can only summarize
`PaymentService` honestly after you know what `charge`, `refund`, and
`_validate` each do. Post-order guarantees that when the parent's turn comes,
every child's summary is **fresh, from this run** — quality flows upward in one
pass, no second sweep needed. Same tree, same group-flattening, same depth
semantics, opposite direction: one shared `walk(order="pre"|"post")` in the
traversal module serves all three tools.

## Dendrogram

```
agent v3
│
├── shared/ ───────────────── machinery both tools stand on
│   ├── 01 post-order plan    walk(order=post) · depth + WOQL max · skip rules · caps
│   ├── 02 run artifact       ONE ToolRun/RunItem schema for both tools → one checklist renderer
│   └── 03 write safety       origin tags · overwrite semantics · run-level undo (commit ranges)
│
├── describe/ ─────────────── the context farmer
│   ├── 01 tool spec          args · estimate (exact: 1 call/node) · flow
│   └── 02 prompt & context   2–3 sentences with a first-sentence contract · leave-blank fallback
│
├── document/ ─────────────── the overview writer
│   ├── 01 tool spec          args · estimate · post-order so parents cite child docs
│   └── 02 prompt & sections  fixed skeleton (what/why/usage/role/children-interaction)
│                             · call-edge grounding · <user_intent> lens
│
└── frontend/
    └── 01 checklist UI       live run checklist · bottom-up fill · undo button · doc links
```

## Decisions inherited from v2 (not re-argued here)

Estimate → confirm gate with knobs (harness/03) · pin branch+commit at run start ·
persist per item, truthful partials · degrade-never-abort *except* where noted
(describe deliberately breaks this rule — describe/02) · `structured_call`
try→retry-with-errors · context via the factory presets (context-engineering/02) ·
prompts in the registry with per-prompt versions · artifacts as mirror docs on the
multi-doc stream.

## The quality gradient (why describe comes first, always)

```
describe  →  document  →  walkthrough
(farms the one-liners)  (eats fresh descriptions,   (eats both)
                         writes the overviews)
```

Descriptions are the raw material of every other tool's context: `<children>`,
`<siblings>`, `<parent>` lines and NodeCards are all built from them. Running
describe over a subtree is *farming context*. The orchestrator prompt encodes the
ordering; empty descriptions in enrichment blocks are the agent's cue to suggest
it before a tour or a doc run.

## One design divergence, flagged for review

**User intent flows into `document_nodes` but deliberately *not* into
`describe_nodes`.** Docs are reading material — angling emphasis toward the
user's question (the walkthrough's `<user_intent>` lens, same rules: never skip,
never distort, grounding senior) makes them better. Descriptions are **canonical
shared context**: every future prompt for every future user is built from them
blindly. A description angled toward "how do retries work" quietly misleads the
next person who asks about validation. Where the user's intent *does* help
describe runs: the agent uses it to pick the node and the depth. If dogfooding
shows this is too strict, the lens can be added later — the seam is one prompt
slot; removing poisoned descriptions later is much harder.

## Build order

| Phase | Contents | Demo gate |
|---|---|---|
| **A — Describe** | shared post-order walk · ToolRun artifact + repo · `describe_nodes` · checklist renderer | "Describe everything under `payments/`, depth 2" → confirm ~30 calls → checklist fills bottom-up → re-run a walkthrough: child lines visibly better |
| **B — Document** | `document_nodes` · call-edge context (factory gains `calls` include) · doc viewer links | "Document `PaymentService` — I care about the retry path" → doc whose *children-interaction* section cites real call edges, retry parts emphasized |
| **C — Safety polish** | run-level undo (revert endpoint + button) · overwrite mode · evals (validator first-pass rate, % described) | run describe twice: second run skips existing; undo the first run: graph back to before, artifact says so |
