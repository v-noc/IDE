# 01 — Mock mode must use the REAL selected node

> ⚠ **SUPERSEDED by [11-backend-only-mock.md](11-backend-only-mock.md)** (2026-07-09).
> The frontend mock generator this doc describes is being **deleted**: the backend
> pipeline with the `fake` provider is the one and only mock, so switching to a real
> LLM never touches the frontend. Do not implement or extend anything below; kept
> for history only.

## The problem (what the user sees)

Today `mockSource` (in
`src/frontend/src/features/Dashboard/features/Agent/walkthrough/source/mockSource.ts`)
ignores the request and replays one of two **hardcoded fixture files**
(`fixtures/smallFunction.json`, `fixtures/classWithCall.json`). Those fixtures contain
made-up node ids like `services/payment/PaymentService`. So when the tour plays, the
executor tries to select nodes that don't exist in the open project — the canvas shows
the wrong thing (or nothing), and the demo is meaningless.

## The target behavior

Mock mode = **real structure, fake words**:

1. The tour is built from the node the user actually selected, walking the **real
   project data** to the chosen depth. Every `node_id`, `start_line`, `end_line` in
   the session is real — so select/pan/expand/highlight all operate on the real
   canvas and real code in Monaco.
2. Only the LLM output is faked:
   - intro texts = generated lorem-style sentences that mention the real node name,
   - block plans = the node's real line range randomly divided into **2–5 contiguous
     blocks**,
   - block texts = lorem sentences mentioning the block's focus label.
3. Frames still stream with small delays so the outline fills progressively, exactly
   like a real backend run.

The old JSON fixtures stay **only** as unit-test inputs. The runtime never imports
them again.

## Files

| File | Action |
|---|---|
| `walkthrough/source/mockGenerator.ts` | NEW — builds a real `WalkthroughSession` + frame list |
| `walkthrough/source/mockSource.ts` | REWRITE — use the generator, drop fixture imports |
| `walkthrough/source/lorem.ts` | NEW — tiny deterministic-ish lorem helpers |
| `walkthrough/fixtures/*.json` | KEEP (tests only). Verify nothing outside tests imports them when done |

## Step A — verify what data the frontend really has (do not skip)

Before writing the generator, open and read these — the generator depends on them:

1. `src/frontend/src/types/project.ts` — confirm the node tree fields: `children`,
   `lazy_child_ids`, `position` (`line_no`, `end_line_no`), `node_type`, and on call
   nodes `target` (a FunctionNode). Note: **groups** have `node_type: "group"` and
   must be walked through transparently.
2. `src/frontend/src/features/Dashboard/service/codeDescendants/` — find the exact
   exported names (there is a query-options builder and a normalize helper; the
   CanvasView already uses them — copy its usage pattern, do not invent parameters).
3. `src/frontend/src/features/Dashboard/utils/findNodeWithDescendantCache.ts` — this
   is how `ensureOnCanvas` finds a node including cached descendants. The generator
   should locate the start node the same way.

Write down (in a comment at the top of `mockGenerator.ts`) which of these you used.

## Step B — `buildMockVisitList`

```ts
async function buildMockVisitList(
  queryClient: QueryClient,
  projectData: ProjectNodeTree,
  projectKey: string,
  startNodeId: string,
  depth: number,
): Promise<VisitNode[]>
```

Rules (this mirrors the backend traversal in
`plan/walkthrough-agent/03-traversal.md` — read that file first):

1. Find the start node (`findNodeByIdWithDescendantCache`). If not found, try the
   lineage fetch the way `ensureOnCanvas.ts` does. If still not found, throw — the
   Launcher shows the error.
2. Depth-first walk. For each node:
   - `group` nodes are **transparent**: recurse into their children at the SAME
     level, they are never a stop.
   - `folder` / `file` → container stop (`has_code: false`).
   - `function` / `class` → code stop when `position` exists:
     `start_line = position.line_no`, `end_line = position.end_line_no`,
     `line_count = end - start + 1`, `gated = line_count >= 8`.
   - `call` → a stop using the **call node's own id** as `node_id`; line data comes
     from `target`'s position when present. `target_id = target?.id ?? null`.
3. **Duplicate rule** — keep a `Map<string, number>` (`explained`). The key is
   `target_id` for calls, the node's **own id** for functions/classes. First
   encounter → `mode: "full"`, record the order. Later encounter (or a call with no
   target) → `mode: "contextual"`, `first_seen_order` = recorded order (or null),
   `has_code: false`, `gated: false`, and **do not recurse into its children**.
4. Children order: sort by `position.line_no` when present (source order); nodes
   without a position go last, alphabetical. Only recurse while `childLevel <= depth`.
5. If a node has `lazy_child_ids` but empty/missing `children`, fetch children with
   the codeDescendants query via `queryClient.fetchQuery(...)` (Step A #2 pattern).
   Wrap in try/catch — on failure, continue with what is loaded (mock mode must
   never hard-fail on a fetch).
6. Fill every `VisitNode` field from `walkthrough/types.ts` — run the zod
   `visitNodeSchema.parse` on each one as you build it. If parse fails, the field
   mapping is wrong; fix the mapping, not the schema.

## Step C — `generateMockFrames`

```ts
function generateMockFrames(session: WalkthroughSession): { delay: number; frame: Frame }[]
```

1. Frame 0: `hello` with the full session (`node_steps: []`, real `visit_list`).
2. Then per visit node, in order, mirroring the backend patcher exactly (ops shapes
   are in `plan/walkthrough-agent/04-data-types.md`):
   - `{op:"add", path:"/node_steps/-", value:<NodeSteps skeleton>}`
   - `{op:"replace", path:"/node_steps/<i>/intro_text", value:<lorem intro>}` +
     `{op:"replace", path:"/node_steps/<i>/degraded", value:false}` (same frame)
   - full code stops only: random `count = 2..5`, but never more than
     `max(2, min(5, floor(line_count / 2)))` so every block has ≥ 2 lines when
     possible. Split `[start_line..end_line]` into `count` **contiguous,
     non-overlapping** ranges that cover it fully. One `add /blocks/-` op per block
     (`focus`: pick from a small label list — "setup", "core logic", "error
     handling", "result" — plus the range).
   - then one `replace /blocks/<j>/text` frame per block with 2–3 lorem sentences
     that include the focus label.
   - Note `<i>` is the index in `node_steps` (append order), which equals the visit
     position in this generator — but compute it by counting your own `add` ops, do
     not assume.
3. Last frames: `{op:"replace", path:"/status", value:"complete"}` patch, then
   `{kind:"end", status:"complete"}`.
4. `seq` starts at 0 and increases by 1 per patch frame — the store logs a warning on
   gaps; there must be none.
5. Delays: 150–500 ms random per frame (0 for hello). Keep a fixed seed or simple
   `Math.random()` — determinism is not required here, valid ops are.
6. Ungated code stops still get exactly **one** block covering the whole range (that
   is how the real pipeline behaves — see `single_block_plan` in
   `src/backend/app/walkthrough/fallbacks.py`).

## Step D — rewrite `mockSource`

- `estimate(req)`: run `buildMockVisitList`, return exact `node_count`, and estimates
  computed the same way as `plan/walkthrough-agent/03-traversal.md` (§ estimate).
- `run(req, onFrame, signal)`: build visit list → build session object (fill
  `WalkthroughSession` fields; `id: "mock-" + Date.now()`, `branch: "main"`,
  `commit_id: "mock"`, `model_id: "mock:lorem"`) → `generateMockFrames` → loop with
  the existing abortable `sleep`, calling `onFrame`.
- It needs `queryClient` and `projectData`. The source interface takes neither — get
  them the way the executor does: `useProjectStore.getState().projectData` and export
  a module-level `queryClient` from `src/frontend/src/lib/queryClient.ts` (it already
  exists — `useTabStore` imports it; reuse THAT import, do not create a new client).

## Prove it

1. `yarn test` still green (fixtures are still valid test inputs).
2. Manual: open a real project → select a real class → depth 1 → Estimate shows a
   node count that matches what you can count on the canvas → Generate → the outline
   lists the REAL child names → play → canvas pans to the real nodes, Monaco opens
   the real code, highlights sit inside the function's real line range, popup text is
   lorem.
3. Select a function under 8 lines → its tour has exactly one block (whole body).
4. Select a node whose children were never expanded on canvas (lazy) → generation
   still lists them (the fetchQuery path) or degrades without crashing.
