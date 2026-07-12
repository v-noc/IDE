# 18 — LangGraph orchestration + LangSmith tracing

> Implements what plan 05 always promised and the first pass skipped: the pipeline
> as a LangGraph `StateGraph`. Payoff: LangSmith shows **one run tree per tour**
> (named spans `intro` / `block_plan` / `explain_block`, each LLM attempt a child
> run with its exact prompt, response, latency, tokens) instead of ~35 disconnected
> root traces. `langgraph>=1.2.9` is already in `pyproject.toml` — no new deps.
>
> **The acceptance gate for this whole fix: frame-for-frame identical output.**
> The existing pipeline tests must pass **unchanged**. If a test needs editing to
> go green, the conversion is wrong, not the test.

Follow the README ground rules: open every file before editing, find code by
searching for the quoted snippet, one step at a time, verify by running.

## Reality check (measured 2026-07-11 — re-verify, don't trust)

- `src/backend/app/walkthrough/pipeline.py` — `run_pipeline(session, patcher, *,
  code_service, contexts)` is a plain `for visit in visit_list.nodes:` loop. All
  the per-stop logic this fix redistributes into nodes lives here; **reuse it,
  don't rewrite it** (the helpers `_load_numbered_code`, `_record_errors`, the
  block-text context construction, the fallback branches are all correct).
- `src/backend/app/walkthrough/graph.py` — **this is the code graph, not the run
  graph.** Do not touch it; the new module gets a different name.
- LangSmith env: LangChain reads `os.environ`, and pydantic-settings does **not**
  export `.env` values into `os.environ`. Boot must bridge that (Step D).

## Step A — state and module layout

New file: `src/backend/app/walkthrough/orchestrator.py`

Two hard rules from plan 05:

1. **State stays JSON-ish scalars + the current plan.** LangSmith records state at
   every super-step; live objects (patcher, services) and bulky contexts would be
   serialized into every trace. Those ride in `config["configurable"]` instead.
2. **Edges are code decisions.** Routing functions read state scalars only.

```python
from typing import TypedDict

from app.walkthrough.schemas import BlockPlan


class WalkState(TypedDict):
    cursor: int                 # index into visit_list.nodes
    total: int                  # len(visit_list.nodes)
    # per-stop scratch — written by the intro node, read by routers
    stop_mode: str              # "full" | "contextual"
    stop_has_code: bool
    stop_gated: bool
    plan: BlockPlan | None
    plan_degraded: bool
    block_cursor: int
```

`config["configurable"]` carries: `patcher`, `code_service`, `contexts`
(the `dict[int, NodeContext]`), `visit_list`, and `errors` (a plain mutable
`list[str]` — the accumulated error log, shared across nodes without reducer
machinery).

## Step B — nodes and edges (move the loop body, don't rewrite it)

Each node is an `async def node(state, config) -> dict` returning only the state
keys it changes. The bodies are cut-and-paste relocations from the current
`run_pipeline` loop — find each quoted piece there first:

- **`intro`** — the code from `await patcher.open_node_steps(...)` through
  `await patcher.set_intro(...)`: opens the NodeSteps skeleton, loads + trims code
  onto the context, runs the intro `structured_call`, records errors, emits.
  Returns the per-stop scratch (`stop_mode`, `stop_has_code`, `stop_gated`) and
  resets `plan=None`, `plan_degraded=False`, `block_cursor=0`.
- **`single_block`** — the `if not visit.gated:` branch: `plan =
  single_block_plan(visit)`.
- **`block_plan`** — the gated branch verbatim: code-unavailable → `even_split_plan`
  (degraded); otherwise `structured_call("block_plan", ...)` with the validator;
  `None` result → `even_split_plan` (degraded).
- **`explain_block`** — ONE block per invocation, exactly the current inner loop
  body for `plan.blocks[state["block_cursor"]]`: `patcher.add_block(...)`, build
  the block-text context (same fields, same `previous_block_lines` format —
  derive the previous lines from `plan.blocks[: block_cursor]` so it matches what
  the loop accumulated), `structured_call("block_text", ...)`,
  `patcher.set_block_text(...)`. Returns `block_cursor + 1`.
- **`advance`** — returns `cursor + 1`. Pure code, no emits (the loop had none
  here either — do not invent a `node_done` frame; frame parity is the gate).

Routing functions (plain code on state):

```python
def route_after_intro(state) -> str:
    if state["stop_mode"] == "contextual" or not state["stop_has_code"]:
        return "advance"
    return "block_plan" if state["stop_gated"] else "single_block"

def route_after_explain(state) -> str:
    assert state["plan"] is not None
    return "explain_block" if state["block_cursor"] < len(state["plan"].blocks) else "advance"

def route_after_advance(state) -> str:
    return "intro" if state["cursor"] < state["total"] else END
```

Wiring: entry → `intro`; `intro` →(route_after_intro); `single_block` →
`explain_block`; `block_plan` → `explain_block`; `explain_block` →
(route_after_explain); `advance` → (route_after_advance). Compile once at module
level (`GRAPH = builder.compile()`), no checkpointer.

## Step C — run_pipeline becomes a thin wrapper (signature unchanged)

File: `src/backend/app/walkthrough/pipeline.py`

`run_pipeline(session, patcher, *, code_service, contexts)` keeps its exact
signature (service.py must not change). Inside:

1. Empty visit list → return the mirror copy as today, no graph invocation.
2. Otherwise:

```python
    errors: list[str] = list(session.error_log)
    config = {
        "configurable": {
            "patcher": patcher,
            "code_service": code_service,
            "contexts": contexts,
            "visit_list": session.visit_list,
            "errors": errors,
        },
        # LangGraph default is 25 super-steps — one stop consumes several, so any
        # real tour dies mid-stream with GraphRecursionError without this.
        "recursion_limit": len(session.visit_list.nodes) * 10 + 50,
        "run_name": f"walkthrough {session.visit_list.nodes[0].name}",
        "metadata": {
            "session_id": session.id,
            "project_id": session.request.project_id,
            "depth": session.request.depth,
            "model_id": session.model_id,
            "prompt_version": session.prompt_version,
            "schema_version": session.schema_version,
        },
    }
    await GRAPH.ainvoke(initial_state, config)
```

3. Finish exactly as today: `session = patcher.mirror.model_copy(deep=True)`,
   `session.error_log = errors`, return.

LLM child runs nest under node spans automatically — LangChain's async tracing
context propagates through `structured_call`; nothing to pass.

## Step D — LangSmith settings + boot bridge (opt-in by key)

1. `src/backend/app/config/settings.py`:

```python
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "v-noc-walkthrough"
```

2. `src/backend/app/main.py`, in `lifespan` next to `validate_llm_settings()`:
   if the key is set, `os.environ.setdefault(...)` for `LANGSMITH_TRACING="true"`,
   `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`. No key → nothing exported → tracing
   off, zero behavior change. Never log the key.

## Step E — tests

- **The gate:** `uv run pytest tests/unit/walkthrough -q` — existing pipeline
  tests pass **unchanged**.
- Add one long-tour test: fake provider, a synthetic visit list of ≥ 30 stops with
  blocks (reuse the pipeline-test fixtures' builder), assert it completes — this
  pins the `recursion_limit` sizing so nobody reintroduces the default-25 bug.
- Add one wiring test: `route_after_intro` / `route_after_explain` /
  `route_after_advance` truth tables (cheap, pure functions).

## Prove it

```bash
cd src/backend && uv run pytest tests/unit/walkthrough -q
```

Frame parity, measured not assumed (fake provider — deterministic):

```bash
# before converting (on the pre-change checkout or stash):
WALKTHROUGH_LLM=fake uv run python -m app.walkthrough.cli <project_id> <node_id> 1 > /tmp/frames_before.ndjson
# after:
WALKTHROUGH_LLM=fake uv run python -m app.walkthrough.cli <project_id> <node_id> 1 > /tmp/frames_after.ndjson
diff /tmp/frames_before.ndjson /tmp/frames_after.ndjson   # must be empty
```

Then the payoff check: set `LANGSMITH_API_KEY` in `.env`, restart, run one real
tour, open LangSmith → project `v-noc-walkthrough` → the run named
`walkthrough <node>` → confirm one tree: intro/block_plan/explain_block spans with
LLM children, and the metadata filterable by `prompt_version`.

Anything suspicious that this doc did not tell you to change → README parking lot.
