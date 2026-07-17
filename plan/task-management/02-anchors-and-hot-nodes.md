# 02 — Anchors & Hot Nodes

The anchor lifecycle (create → dangle → re-anchor) and the convergence signal,
both derived from the graph at read time. Nothing in this file stores state;
that is the point.

## Anchor lifecycle

### Create

Three entry points, one service call (`TaskService.add_anchor`):

1. **"New task here"** on a canvas node — anchor pre-filled from the node the
   menu opened on (06).
2. **Detail panel → add anchor** — node search via the existing
   `SelectNodeDialog` machinery / code routes; the picker returns a node id.
3. **Suggested subtasks** — each checked dependency creates a subtask whose
   first anchor is that dependency (06).

At create the service reads the node once and snapshots `qname` + `kind` into
the anchor subdocument. If the node id doesn't exist, the add is refused —
anchors are born resolved.

### Resolution — derived, batched

`is_resolved` is **computed at read time**: an anchor is resolved iff its
`node_id` names a live document. One WOQL existence check per response, batched
over every anchor id in the payload (board read = one query, not N).

Why derived beats stored (the mock stores a boolean):

- The watcher reparses on file change (`core/watcher`); surviving nodes keep
  their ids (`ast_processor.sync_content` updates in place), renamed/deleted
  ones vanish. A stored flag is stale from the first reparse after it was
  written. A derived flag cannot lie.
- v1 needs **zero parser hooks**. The parser pipeline (currently being
  refactored under `plan/parser-orchestrator-refactor/`) is not touched.
- Cost is one indexed id-set lookup, cached with the summary (below).

When unresolved, the UI renders the snapshot (`ƒ main.load_config ⚠`) — the
task never loses its human meaning even though the graph lost the node.

### Re-anchor

Detail-panel action on an unresolved anchor:

1. Backend suggests candidates: name/qname search over live nodes (existing
   code-search paths), seeded with the snapshot qname's last segment
   (`load_config`), same-kind matches ranked first.
2. User picks a candidate (or searches freely). `TaskService.re_anchor`
   replaces `node_id` and refreshes the snapshot in one update; a system note
   is appended ("re-anchored main.load_config → main.load_settings").
3. No auto-re-anchor in v1. A rename detector (same qname tail + same file)
   could propose confidently — but it must stay a *proposal*; silently moving
   a task's meaning is worse than a visible ⚠. Seam for later.

## The hot rule

> A node is **hot** when ≥ 2 distinct open tasks anchor to it, counting
> through the subtask closure, deduped.

Precisely: for each task T that anchors node N (directly or via any member of
T's subtask closure), collect the *root-relevant* open task. Two or more
distinct open tasks in that set → hot. The mock's scenario: `Fix logging bug`
(direct anchor) + `Speed up runner` (direct anchor) + `Refactor dd()`
(subtask of both) on `main.dd` → dedupe still yields ≥ 2 distinct open tasks →
hot, amber, top of Blockers.

## One summary, four surfaces

`GET /projects/{id}/tasks/anchor-summary` (03) returns, in one response:

```json
{
  "nodes": {
    "FunctionSchema/abc123": {
      "qname": "main.dd",
      "open_task_ids": ["TaskSchema/…", "TaskSchema/…"],
      "open_count": 2,
      "hot": true
    }
  },
  "hot_count": 1
}
```

Consumers — all of them read this, none re-derive:

| Surface | Reads |
|---|---|
| Canvas node badge + glow (`NodeHeader`/`EnhancedNode`) | `open_count`, `hot` per node id |
| Node popover task list | `open_task_ids` → titles from the tasks query cache |
| Sidebar tree badges (`TreeNode/NodeRow`) | `open_count`, `hot` per node id — **exact-node counts in v1** (the mock's sidebar shows `dd 3`, not a rollup); subtree rollups for folders are a later refinement |
| Board header (`6 open · 1 hot node`) + Blockers section | `hot_count`; Blockers = nodes sorted by `open_count` desc, hot first |

Computation lives in `TaskService.anchor_summary`: load open tasks (status in
non-`is_done` columns), walk closures with a visited set, group anchors by
`node_id`, run the batched existence check (unresolved anchors are excluded
from hotness — a dangling anchor can't make a live node hot, and the node is
gone anyway).

## Caching & invalidation

- Same `fastapi-cache` `DEFAULT_TTL` decorator the document routes use.
- Every `TaskService` write that can change the summary (create, delete,
  status move, anchor add/remove/re-anchor, subtask edge change, column
  `is_done` change) bumps a per-project cache key and emits a socket event
  `tasks.summary_changed` through the existing socket layer — the frontend
  invalidates its react-query key and refetches (04).
- Reparse can also change the summary (nodes vanish → anchors unresolve).
  v1 accepts TTL staleness here (badge corrects within the TTL or on next
  task write); the seam is one `tasks.summary_changed` emit at the end of the
  parser's commit batch, which the parser-refactor's scheduler can own later.

## Blockers ranking (sidebar section)

Straight read of the summary: nodes with `open_count >= 2`, sorted by
`open_count` desc then qname. Each row: kind icon, qname, amber count — click
focuses the node on canvas (existing focus + auto-expand actions). No new
endpoint; it is the same payload the badges already fetched.
