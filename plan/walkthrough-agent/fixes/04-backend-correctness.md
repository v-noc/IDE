# 04 — Backend correctness fixes

All paths under `src/backend/`. Three of these already have failing tests — run
`uv run pytest tests/unit/walkthrough -q` before you start and confirm you see the
same 3 failures listed in the README.

---

## B1 — `pipeline.py` imports a module that is not in the tree

**Where:** `app/walkthrough/pipeline.py` line ~5:
`from app.walkthrough.context import (...)`.

**Wrong:** there is **no `app/walkthrough/context.py`** in the working tree — the
imported names (`NodeContext`, `build_context`, the six prompt builders) actually
live in `app/walkthrough/prompts.py`. The import happened to work on the dev machine
(probably a stale artifact); it will crash on a fresh clone, and `api/root.py`
imports the walkthrough router at startup, so the **whole backend would fail to
boot**.

**Fix (do all three):**
1. Change the import to `from app.walkthrough.prompts import (...)` with the same
   names. Confirm every imported name exists in `prompts.py` (open it and check).
2. Hunt the stale artifact: `find app/walkthrough -name "*context*"` and
   `find app/walkthrough/__pycache__ -name "*.pyc" | xargs ls -la` — delete any
   `context`-named leftovers, then `find . -name __pycache__ -exec rm -rf {} +` once.
3. Prove from a clean interpreter:
   `uv run python -c "import app.walkthrough.pipeline; print('ok')"` — and run it
   again after deleting all `__pycache__` dirs.

---

## B2 — `over_cap` can never become true (failing test)

**Where:** `app/walkthrough/traversal.py`.

**Wrong, two layers:**
1. `visit()` stops appending at `VISIT_CAP` (`if len(visits) >= VISIT_CAP: return`),
   so `node_count` maxes out at exactly 40 — and `compute_estimate` checks
   `node_count > VISIT_CAP`, which is then never true. A too-big subtree silently
   truncates into a "complete-looking" 40-stop tour instead of blocking Generate.
2. `depth = min(depth, MAX_DEPTH)` caps depth at 3 — fine — but the failing test also
   shows a deep chain never reaches the cap because of the clamp. The cap must be
   about **width**, not defeated by the clamp.

**Fix:** count without truncating the decision:
- Add a counter that keeps incrementing even when you stop appending, OR simpler:
  walk fully but stop **appending** past the cap while setting a boolean
  `truncated = True`; return it on `VisitList` (add field `truncated: bool = False`
  to the schema) and make `compute_estimate` use
  `over_cap = visit_list.truncated or len(nodes) > VISIT_CAP`.
- Update `test_over_cap_flag` expectations only if the test itself contradicts the
  chosen design (it builds a deep chain with `depth=VISIT_CAP+5`; with the depth
  clamp at 3 a **chain** can never exceed the cap — rewrite the fixture as a WIDE
  tree: one file with 50 function children at depth 1). The assertion
  `est.over_cap is True` stays.
- Frontend: `over_cap` already disables Generate; nothing to do there. But note the
  new `truncated` field must be added to the frontend zod `visitListSchema` as
  `.optional()` **or** always emitted by the backend — pick always-emitted, and add
  it to `walkthrough/types.ts` accordingly (keep the two schemas identical).

**Prove:** `test_over_cap_flag` passes; the other traversal tests still pass.

---

## B3 — duplicate/recursion rule silently depends on `target_id` (failing test)

**Where:** `app/walkthrough/traversal.py` — `tid = node.target_id` and the
`explained` map; `app/walkthrough/graph.py` `_target_id()` fills `target_id` with the
node's own id for functions/classes.

**Wrong:** the traversal's duplicate rule only works when every function/class
`GraphNode` has `target_id` set — which `graph_node_from_domain` does, but nothing
else guarantees. The failing test builds `GraphNode` fixtures directly (no
`target_id`), and recursion breaks: the self-call gets `mode="full"`. Splitting one
rule across two files is the actual bug.

**Fix:** make traversal self-sufficient. In `visit()`:

```python
tid = node.target_id
if tid is None and node.kind in ("function", "class"):
    tid = node.id
```

Keep `graph.py` as it is (harmless duplication in the domain mapper is fine).

**Prove:** `test_recursion_is_contextual` passes without touching the test.

---

## B4 — retry knob broken: a fresh LLM is built per attempt (failing test)

**Where:** `app/agent/llm/structured.py` — `make_llm(call_type)` is called **inside**
the `for attempt in range(2)` loop.

**Wrong:** each attempt constructs a new `FakeLLM`, so instance state
(`_attempts`, `fail_first_attempts`) resets and "fail once then succeed" can never
succeed — as the failing test proves. For real providers it would also rebuild the
client per attempt for no reason.

**Fix:** hoist `llm = make_llm(call_type)` above the loop. Nothing else changes.

**Prove:** `test_structured_call_retries_then_succeeds` passes.

---

## B5 — call stops feed the WRONG code to the LLM

**Where:** `app/walkthrough/pipeline.py`, `_load_numbered_code`:
`payload = await code_service.get_code(visit.node_id)`.

**Wrong:** for a `call` stop, `visit.node_id` is the **call node** — `get_code` on it
returns the call site's slice (one line), while `visit.start_line/end_line` (used for
numbering, the block gate, block bounds, and the frontend highlight) come from the
**target function**. Result: the numbered code shown to the model is one mislabeled
line, and block plans/highlights refer to code the model never saw. (The frontend
fetches by `targetKey` for call nodes — the backend must mirror that.)

**Fix:** in `_load_numbered_code`:

```python
code_node_id = visit.target_id if visit.node_type == "call" and visit.target_id else visit.node_id
payload = await code_service.get_code(code_node_id)
```

Also guard the gated path: if `numbered_code is None` for a gated stop, skip the
block-planner call and use the deterministic `even_split_plan` directly, appending
`"code unavailable for <node_id>"` to the error log — never send `(code unavailable)`
to the block planner (search `prompts.py` for that placeholder; it must only ever
appear for block_text degradation, ideally nowhere).

**Prove:** new unit test with a fake `code_service` that records requested ids: a
call visit requests the **target** id. Second assertion: gated visit + `None` code →
no `block_plan` LLM call (fake counts calls) and blocks are the even split.

---

## B6 — validator does not actually detect overlaps

**Where:** `app/walkthrough/validators.py`:

```python
if block.start_line <= last_start: ...
last_start = block.start_line
```

**Wrong:** it only checks that starts strictly increase. Blocks `10–30` and `15–20`
pass (15 > 10) despite overlapping. The 80 % coverage check double-counts overlapped
lines too (a `set` hides it, but the ordering error message is misleading).

**Fix:** track the previous **end**:

```python
last_end = start - 1
for block in sorted(...):
    ...
    if block.start_line <= last_end:
        errors.append(f"block {block.start_line}-{block.end_line} overlaps the previous block")
    last_end = max(last_end, block.end_line)
```

**Prove:** new test: plan with `10–30` + `15–40` inside a 10–50 node fails validation
with the overlap message.

---

## B7 — one bounds formula, three copies

**Where:** `traversal.py::_block_bounds`, `prompts.py::_block_bounds`,
`validators.py::_bounds` — three near-identical implementations of
`min=2, max=clamp(lines//5, 2, 6)`.

**Wrong:** the plan's rule (07-prompting: "prompt and validator must quote the same
numbers") is structurally unenforced; one edit in one copy silently desynchronizes
the prompt from the validator, and the model starts failing validation it was never
told about.

**Fix:** keep exactly one function `block_bounds(line_count)` in `traversal.py`;
import it in `prompts.py` and `validators.py`; delete the copies. Add a 3-line test
pinning a few values: `7 → (2,2)`, `10 → (2,2)`, `30 → (2,6)`.

---

## B8 — misconfigured provider degrades silently instead of failing fast

**Where:** `app/agent/llm/structured.py` (`make_llm` raises `NotImplementedError`
for non-fake providers) + `app/walkthrough/service.py`.

**Wrong:** `structured_call` catches **all** exceptions per attempt — so with
`WALKTHROUGH_LLM_PROVIDER=openai` today, every call raises, every stop falls back,
and the user gets a fully-degraded lorem-grade tour with no error. The plan (backend
02) demands fail-fast on bad provider config.

**Fix:** in `service.py::_stream_run`, before creating the session, call
`resolve_provider()` and `make_llm("intro")` once inside a try/except; on failure
emit `{"kind":"end","status":"error","message":"LLM provider not configured: ..."}`
and return. Keep `structured_call`'s catch-all for genuine call-time failures.

**Prove:** unit/route test with `WALKTHROUGH_LLM_PROVIDER=openai` (no key, not
wired): the stream is exactly one `end/error` frame; no session, no hello.

---

## B9 — the pipeline's final session is thrown away

**Where:** `app/walkthrough/service.py`: `await run_pipeline(session, patcher, ...)`
— return value ignored; `run_pipeline` builds a final session with the accumulated
`error_log` that nobody reads. Token usage is never tracked at all.

**Fix (minimal now, persistence comes later):** capture it —
`final_session = await run_pipeline(...)` — and log a one-line summary via loguru:
session id, stops, degraded count (`sum(ns.degraded or any(b.degraded for b in ns.blocks) for ns in final_session.node_steps)`),
`len(final_session.error_log)`. When persistence (backend plan 04) lands, this is the
object that gets saved; leave a `# TODO(persistence): save final_session` marker.

---

## B10 — small notes (fix opportunistically, no dedicated tests required)

1. `service.py` — the 409 lock is set inside the producer (after streaming starts):
   two rapid POSTs can both pass the check. Move
   `_active_runs[project_id] = ...` reservation into `run()` before returning the
   response (use a placeholder id, replace once the session exists), and make sure
   the `finally` still cleans it up.
2. `loader.py` — `get_code_descendant_nodes(node_id, depth_max=None)` is called for
   **every** BFS node: the same full subtree is fetched N times, and it ignores the
   requested depth. Pass a depth bound and fetch descendants only from the start
   node + call targets; children of already-collected nodes are already in
   `collected`. This is a performance fix; behavior must not change (traversal tests
   stay green).
3. `graph.py::build_graph` — the `if start_id not in by_id and nodes:` block re-adds
   `nodes[0]` which is already in the dict; delete it (dead code) or make it do what
   it meant (nothing needed).
4. `prompts.py::block_text_user_prompt` — the block's **line range** is missing; the
   model only sees the focus label. Add a line:
   `f"Lines {ctx.block_start}-{ctx.block_end}: {ctx.block_focus}"` (add those two
   fields to `NodeContext`; the pipeline already knows them when building the
   text context).
5. `cli.py` calls the private `service._stream_run` — acceptable for now; add
   `--provider fake` style override + `--frames out.ndjson` dump when you touch it
   next (that dump is the frontend fixture recorder).

## Prove it (whole file)

```
cd src/backend
uv run pytest tests/unit/walkthrough -q      # 0 failed, including the 3 previously failing
uv run python -c "import app.api.root; print('boot imports ok')"
```
