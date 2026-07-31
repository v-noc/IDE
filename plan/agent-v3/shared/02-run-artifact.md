# Shared 02 — One Run Artifact for Both Tools

Describe and document runs stream and persist the same artifact shape. One
schema, one repo, one frontend renderer (`render: "run_checklist"`) — the v2
artifact registry's render-hint design exists precisely so two tools can share
one renderer.

## The schema

```python
class ToolRun(BaseModel):
    id: str
    tool: Literal["describe_nodes", "document_nodes"]
    request: dict                        # the validated args, verbatim
    branch: str
    commit_id: str                       # pinned at start — all reads use it
    status: Literal["generating", "complete", "error", "aborted"]
    items: list[RunItem]                 # appended as the plan executes
    written_commits: list[str] = []      # every graph commit this run made (undo — shared/03)
    error_log: list[str] = []
    schema_version: str
    prompt_versions: dict[str, str]      # {"describe.node": "2"} — per-prompt, v2 registry style
    model_id: str
    usage: TokenUsage
    user_query: str = ""                 # document runs only; stored for evals


class RunItem(BaseModel):
    node_id: str
    name: str
    node_type: str
    level: int                           # depth below the start node — lets the UI indent
    state: Literal["pending", "writing", "written", "skipped_existing", "failed"]
    preview: str = ""                    # describe: the first sentence · document: the doc title
    error: str = ""                      # validator message on failure — eval food
```

**Why one schema and not `DescribeRun` + `DocumentRun`.** The differences are one
enum value and how `preview` is filled. Two schemas would mean two repos, two
renderers, two sets of fixtures — for zero expressive gain. When a third batch
tool appears (a staleness sweep, a test-generation run), it slots into the same
shape; that's the definition of the shape being right.

**Why `preview` is on the item.** The checklist is a *live quality window*: the
user watches first sentences appear and can judge the run while it spends —
the same honesty mechanism as watching tour stops fill in. Without previews the
checklist is just a progress bar, and bad output is discovered only after the
bill.

## Streaming

The tool's patcher points at `tool_run/<id>` on the shared conversation stream
(patcher v2, unchanged):

| Moment | Patch |
|---|---|
| run starts | `open` with the full plan as `pending` items — the checklist renders complete and empty immediately, then fills |
| item starts | `replace /items/{i}/state` → `writing` |
| item done | `replace` state → `written` / `skipped_existing` / `failed` + `preview` / `error` |
| run ends | `replace /status` + `close` |

Progress on the **tool part** (`{done, total, label}`) carries the code-authored
label — "describing validate_card (14/32)" — same zero-token liveliness rule as
everything else.

## Persistence

`ToolRunRepo` in `app/core/repository/` (house pattern, registered in
`Repositories`). The run document persists per item state change — a crash
leaves a truthful checklist, and post-order means everything marked `written`
is genuinely finished (shared/01). The `result` dict returned to the agent is
the usual compact summary:

```python
{"run_id": …, "written": 28, "skipped": 3, "failed": 1, "status": "complete"}
```

The agent's closing line writes itself from this — "28 described, 3 already had
text, 1 failed validation" — and the artifact holds everything else.
