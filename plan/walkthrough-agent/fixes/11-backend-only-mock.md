# 11 — One mock, server-side: delete the frontend mock, prove backend blocks

## The decision (read first — this supersedes earlier docs)

There is exactly **one** mock generator from now on: the **backend pipeline running
the `fake` provider**. The frontend always talks to the backend API. Why:

- The backend fake pipeline exercises the REAL traversal, REAL code loading, REAL
  patcher/frames — the frontend cannot drift against a parallel implementation.
- Switching to a real LLM later = change `WALKTHROUGH_LLM_PROVIDER` (+ wire the
  ChatOpenAI branch, backend plan 02) — **zero frontend changes**. That is the whole
  point of the wire protocol.

Supersedes: **fix 01** (frontend mock from real nodes — delete that code now) and
**fix 10's "Mock data" section** (mockOverrides.ts goes away with it; hand-tuned
demo scenarios, if ever needed, become a backend concern). Fix 10's Monaco/popover
pieces are unaffected — they consume store state and don't care who filled it.

## The bug this explains

"Generate only produces node intros, no blocks/highlights." Two stacked facts:

1. `walkthrough/source/index.ts` defaults to **mock unless** `VITE_WALKTHROUGH_MOCK`
   is `"0"`/`"false"`. Unless that env var was set, Generate **never reached the
   backend** — the frontend mockGenerator ran, and its gate reads `node.position`
   from canvas tree data, which is unreliable → `has_code` false → intro-only steps.
2. The backend pipeline DOES have block logic (read `app/walkthrough/pipeline.py`:
   ungated → `single_block_plan`, gated → FakeLLM block planner → per-block texts),
   but **nothing proves it emits block frames** — there is no pipeline-level test.
   Static review says it should work; do not trust that. Part B makes it proven.

## Part A — Frontend: backend is the only source

All paths under `src/frontend/src/features/Dashboard/features/Agent/walkthrough/`.

1. **Delete** `source/mockGenerator.ts`, `source/lorem.ts`, `source/mockOverrides.ts`,
   `source/mockSource.ts`. (Git history keeps them; do not comment them out.)
2. `source/index.ts` becomes:

```ts
import { httpSource } from "./httpSource";
export const walkthroughSource = httpSource;
console.info("[walkthrough] source: http (backend)");
export { applyFrame, applyOpsToSession } from "./applyFrame";
export type { WalkthroughSource } from "./types";
```

   Remove every `VITE_WALKTHROUGH_MOCK` mention (grep the whole frontend for it —
   also `.env*` files and docs).
3. **Fixtures:** `fixtures/*.json` may still be imported by unit tests
   (`flatten.test.ts`, `applyFrame.test.ts`) — check imports. Tests keep them (they
   test frame application, which is source-agnostic). If only mockSource imported
   them, delete them too.
4. `Launcher.tsx`: the estimate already goes through `walkthroughSource.estimate` —
   verify it now hits `GET /api/v1/walkthroughs/estimate` and that
   `VITE_API_BASE_URL` is right in dev (network tab). Backend not running should
   show the estimate error state, not a silent nothing.
5. Nothing else changes: store, executor, popovers all consume frames/state the
   same way regardless of source.

## Part B — Backend: prove (then fix) block generation with the fake provider

### The contract to enforce (this is also where the line cap lives)

For every **full code stop** (`has_code: true`, `mode: "full"`), the stream MUST
contain block frames. The **line gate** (`LINE_GATE = 8` in
`app/walkthrough/traversal.py`) decides the shape:

| Stop | Expected frames after `node_intro` |
|---|---|
| container (folder/file) or contextual | none — intro only (correct today) |
| full code, `line_count < 8` (below the minimum line cap) | exactly **1** `add /node_steps/<i>/blocks/-` op — the whole body as one block — then 1 block-text `replace`. **No block-planner call** (the gate skips it) |
| full code, `line_count >= 8` | between `2` and `max(2, min(6, lines // 5))` block `add` ops (the fake planner even-splits within the bounds the prompt states), then one text `replace` per block |

Every block's `start_line`/`end_line` must lie inside the stop's
`[start_line, end_line]` — these are the numbers the frontend highlights.

### Step B1 — write the missing proof first

New file `src/backend/tests/unit/walkthrough/test_pipeline_blocks.py`:

- Build a small in-memory graph of **parsed domain-shaped GraphNodes** (reuse the
  `_g` helper pattern from `test_traversal.py`): one file → one class → one 40-line
  function (gated), one 5-line function (below the cap), one call whose target is
  the 40-line function (→ contextual).
- Fake `code_service`: `get_code(id)` returns `{"code": "<n lines of text>"}`
  matching each node's line span; record which ids were requested (asserts the
  call-stop fix: calls request their **target's** id).
- Run `run_pipeline` with the `fake` provider and a **recording patcher** (wrap the
  real `Patcher` with an `emit` that appends frames to a list — the real class, not
  a stub, so op paths are the real ones).
- Assert, per the contract table: count of `add .../blocks/-` ops per stop; every
  block inside the stop's range; every block text non-empty; contextual stop has
  zero block ops; the 5-line function produced **no** `block_plan` LLM call (count
  calls in the fake) and exactly one block.

Run it. **If it passes**, the backend was fine all along and Part A alone fixes the
user-visible bug. **If it fails**, fix in this order (most likely first):

1. `traversal.py` — `has_code`/`gated` per stop: print the visit list in the test;
   if `has_code` is false for the function, the break is in
   `graph.py::graph_node_from_domain` (position mapping) or the test graph itself.
2. `pipeline.py::_load_numbered_code` returning `None` (gated stop then must fall
   back to `even_split_plan`, never skip blocks silently — verify that guard exists;
   it was added as fix 04-B5).
3. `agent/llm/fake.py` — the regexes that read bounds from the prompt
   (`between (\d+) and (\d+) blocks`, `lines (\d+)[–-](\d+)`) must match the actual
   prompt wording in `prompts.py` (`Choose between X and Y blocks.`, `The function
   spans lines A–B.`). If someone rewords the prompt, the fake silently degrades —
   add one test asserting the fake parses the real prompt builders' output.

### Step B2 — make the fake demo look real (small, optional but wanted)

In `fake.py`, the block count currently collapses to the minimum. Make it vary:
`count = min_blocks + (stable_hash(node_name) % (max_blocks - min_blocks + 1))` —
seeded by the node name so the same node always gets the same split (repeatable
demos, varied across nodes, 2–5 in practice). Keep the even split of ranges.

### Step B3 — end-to-end check (manual, once)

Backend running with `WALKTHROUGH_LLM_PROVIDER=fake` (the settings default):

```
uv run python -m app.walkthrough.cli <project_id> <node_id> 1 | grep -c '"blocks/-"'   # > 0
uv run python -m app.walkthrough.cli <project_id> <node_id> 1 --estimate-only          # visit_list shows has_code/gated true for code stops
```

Then in the app (after Part A): Generate on a class → outline grows block sub-rows,
block steps show Monaco highlights. A function under 8 lines shows exactly one
block covering its whole body — that is the minimum line cap working, not a bug.

## Prove it (whole doc)

- [ ] `grep -rn "VITE_WALKTHROUGH_MOCK\|mockGenerator\|mockSource" src/frontend/src` → only test files (or nothing).
- [ ] Network tab on Generate: `POST /api/v1/walkthroughs/run` streaming NDJSON.
- [ ] `uv run pytest tests/unit/walkthrough -q` green, including the new
      `test_pipeline_blocks.py`.
- [ ] In-app: gated function → 2–5 blocks with highlights; small function → 1 block;
      contextual call → intro only.
- [ ] Flip `WALKTHROUGH_LLM_PROVIDER=openai` (unwired): stream is a single honest
      `end/error` frame (04-B8), frontend shows the error — still zero frontend
      changes needed for provider switching.
