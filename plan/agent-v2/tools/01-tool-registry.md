# Tools 01 — The Tool Registry

How tools are declared, how they become LangChain tools, and what it takes to add
one. The registry is designed so that the *second* tool (and the tenth) is a spec
plus a module — no harness changes.

## Taxonomy: query tools vs task tools

| | Query tool | Task tool (subagent) |
|---|---|---|
| Purpose | put facts into the agent's context | produce an artifact (tour, docs…) |
| LLM calls | **zero** | many, via its own micro-pipelines |
| Streaming | none — result returned whole | patches its own artifact doc + progress |
| Estimate / confirmation | never | **required** / per policy |
| In this build | **none shipped** (search/query skipped — the attached node is the id source) | `walkthrough` |

**Why keep the taxonomy even though this build ships one tool.** The line decides
where machinery lives: everything about cost, confirmation, artifacts, and
degradation attaches to *task* tools only. When query tools arrive (`get_node`,
`search_nodes`), they skip all of it by construction — free to call liberally.

A **task tool is a subagent** in the pipeline sense: its own graph, own model
config, own retry/fallback policy, own artifact doc, own prompt versions. What it
is *not*: conversational. It cannot ask questions mid-flight (anything it would
ask must be an arg, surfaced at confirmation time), and it never emits chat parts.

## ToolSpec

```python
# app/agent/tools/base.py

class ToolSpec(BaseModel):
    name: str                            # "walkthrough"
    description: str                     # MODEL-FACING: when to use it, what it returns
    input_model: type[BaseModel]         # args schema — one source of truth (see below)
    kind: Literal["query", "task"]
    confirmation: Literal["never", "over_threshold", "always"]
    render: str | None                   # ArtifactRef.render hint for the frontend
    handler: QueryHandler | TaskTool


class TaskTool(Protocol):
    async def estimate(self, args, services) -> ToolEstimate    # pure code, no LLM
    async def run(self, args, services) -> ToolOutcome          # streams patches while running


class ToolEstimate(BaseModel):
    items: int                           # exact — the plan is deterministic
    llm_calls: int                       # honest guess ("~30")
    label: str                           # "12 stops · ~30 LLM calls" — the confirm card line
    over_cap: bool                       # refuse outright, message says how to shrink
    knobs: dict = {}                     # {"depth": {"value": 2, "max": 3}, "verbosity": "quick"}


class ToolOutcome(BaseModel):
    result: dict                         # compact, model-facing (data-model/01)
    artifact: ArtifactRef | None
    degraded: bool = False
```

## Decision: generate LangChain tools from specs — don't write them twice

```python
# app/agent/tools/base.py
def langchain_tools(registry) -> list[BaseTool]:
    # for each spec: StructuredTool.from_function(...) with
    #   name/description from the spec,
    #   args_schema = spec.input_model,
    #   coroutine   = a harness shim that injects services and routes
    #                 task tools through the estimate/confirm middleware path
```

**Why.** `input_model` doing double duty — Pydantic validation on our side *and*
the tool schema the model sees via `bind_tools` — means the args the model was
shown and the args we validate can never drift apart. The alternative (hand-written
tool functions per tool plus separate specs) is the double work Yared explicitly
ruled out; LangChain's `StructuredTool` exists precisely for this.

Services (`ProjectUoW`/`Repositories`, the patcher, settings) are **injected by the
shim**, never listed in `input_model` — the model only ever sees real arguments.

## Adding a tool — the checklist

1. Write `input_model` (Pydantic, every field described — descriptions are prompt
   text for the model).
2. Implement the handler: `estimate()` (task tools) + `run()`, following the shared
   template: deterministic plan → per-item micro-pipeline via
   `app/agent/llm/structured.structured_call` → persist + patch per item → compact
   summary.
3. Register a `ToolSpec` in the registry module.
4. Add its prompts to the prompt registry with a version (prompts/01).
5. Add the artifact doc type + repo if it produces one, and a `render` hint.
6. Fixtures: one estimate test, one degraded-path test, one prompt-budget test.

Nothing in the harness, the stream adapter, the patcher, or the routes changes.
That is the definition of done for this design.

## Cross-cutting rules (every task tool, memorized once)

| Rule | Detail |
|---|---|
| Plan is code | which items, in what order — never the model's decision |
| Pin at start | capture `branch` + `commit_id` before planning; all reads use it; the artifact records it |
| Persist per item | a crash leaves a truthful partial artifact |
| Degrade, never abort | per-item failures fall back and flag; summary carries `degraded_count`; artifact keeps `error_log` |
| Cancellation is cooperative | checked between items; artifact status `aborted`; summary says how far it got |
| Idempotent re-run | re-run after a crash is always the answer (walkthrough: a new session) |

## Growth path (tracked, not built)

| Future tool | What's already in place |
|---|---|
| `get_node` / `list_children` (query) | NodeCard shape = `NodeRefPart` fields + description; known-ids set already tracks tool results |
| `search_nodes` (query, lexical → semantic) | same card shape; the agent prompt already prefers attached nodes first |
| `describe_nodes` (task) | **planned in full — `plan/agent-v3/`** (post-order traversal, first-sentence contract, leave-blank fallback) |
| `document_nodes` (task) | **planned in full — `plan/agent-v3/`** (fixed overview skeleton, call-edge grounding, intent lens) |
| background long tasks | the tool part's `progress` shape already fits; needs a task registry + status endpoint |
