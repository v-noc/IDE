# v2 · 00 — Vision & Architecture

Read this first. It is the map; [08](08-backend-spec.md) and
[09](09-frontend-spec.md) are the step-by-step build instructions;
01–07 are the reference specs (pixels, tokens, interactions) you consult
while executing 08/09.

## Vision (one paragraph)

V-NOC tasks are **anchored to the code graph**: a task points at the
functions/classes/files it is about. The board is a normal kanban; the
payoff is on the canvas — when two or more open tasks converge on one
node, that node glows **hot** before the merge conflict happens. v2 makes
the shipped feature (a) actually work (mutations persist, board refreshes)
and (b) look and behave exactly like the approved mock
(`~/Downloads/taskmangment/V-NOC Tasks.dc.html`).

## System shape

```
frontend                              backend
────────                              ───────
Tasks tab (board)  ─┐
Detail panel        ├─ react-query ── /api/v1/tasks/* ── TaskService ── TaskRepo/BoardRepo ── TerminusDB
Canvas badges/glow  │   (one board      (routes:            (ALL rules      (schema:            (project db,
Node popover        │    query +         thin, ids in        live here)      TaskSchema          current branch,
Sidebar chips       │    one summary     QUERY params)                       self-links)         commits)
New-task modal     ─┘    query)
        ▲
        └── socket "tasks.changed" / "tasks.summary_changed" → invalidate queries
```

**Two server reads power every surface:**

1. `GET /tasks/board` → `{ board: {columns…}, tasks: [enriched task…] }` —
   the whole payload; board, detail panel, popover, modal search all read
   from this one react-query cache.
2. `GET /tasks/anchor-summary` → `{ nodes: {node_id: {open_count, hot,
   open_task_ids, qname}}, hot_count }` — canvas badges, sidebar chips,
   hot styling, board summary.

**One mutation set** (create, update, move, subtask link/unlink, blocked-by,
anchor add/remove/move, note) — every surface calls the same hooks; no
surface owns private data paths.

## The invariants (laws — every implementation step must preserve these)

| # | Law | Where enforced |
|---|---|---|
| L1 | Tasks point at nodes; nodes never point at tasks. Anchors are **soft refs** (`node_id` + qname/kind snapshot) because the parser deletes code nodes at will | schema + service |
| L2 | Task→task edges (`subtasks`, `blocked_by`) are **real TerminusDB self-links** `Set["TaskSchema"]` — never JSON blobs ([06](06-subtasks-as-self-references.md)) | schema |
| L3 | **A call is never an anchor.** Any `CallSchema/…` id entering an anchor flow resolves server-side to `target_function ?? target_class`; dangling target → 422 ([07](07-subtasks-and-node-selection.md)) | `_snapshot_anchor` |
| L4 | Anchor ops are **idempotent and keyed by `node_id`** — never by list index. Add-existing = no-op; remove-absent = no-op; a task's anchors are unique by node_id | service |
| L5 | Resolution (`is_resolved`) and hotness are **derived at read time**, never stored | enrichment |
| L6 | The subtask/blocked-by graph is a **DAG** — every edge add runs the cycle check and refuses with a sentence the UI shows verbatim | service |
| L7 | Task ids (`TaskSchema/uuid`) contain `/` → they **never appear in URL path segments**; always query params (`?task_id=`) | routes + api client |
| L8 | Task GET responses are **never cacheable**: no `@cache` decorator, no `Cache-Control: max-age` — freshness comes from react-query invalidation + socket events | routes |
| L9 | Hot = **≥2 distinct open tasks** anchored to a node, counted through the subtask closure, deduped | anchor_summary |
| L10 | Every visual value comes from `Tasks/theme.ts` ([01](01-design-tokens.md)); the mock wins over v1 plan text | frontend |

## Data model (final shape)

```
BoardSchema/default          TaskSchema/{uuid}
  columns_json  (value)        key           "VN-7"        (minted, immutable)
  task_counter                 name          title
                               description
                               task_type     epic|task|bug|improvement
                               status        column id
                               priority      none|low|medium|high|urgent
                               rank          LexoRank string, scoped to column
                               labels_json   (value)
                               subtasks      Set[TaskSchema]   ← self-links (L2)
                               blocked_by    Set[TaskSchema]   ← self-links (L2)
                               anchors_json  [{node_id, qname, kind}]  ← soft (L1)
                               notes_json    [{text, at, origin}]
                               created_at / updated_at
```

Derived on the wire only (L5): `anchors[].is_resolved`, `subtasks[]`
(id/key/title/status/shared), `subtask_progress {done,total}`,
`blocked_by[]` enriched, `blocks[]` enriched, `blocked`.

## The tricky operations (why they get their own algorithms in 08)

These are the places a naive implementation goes wrong; 08 gives each a
numbered algorithm — do not improvise them:

- **Anchor add** — must resolve calls (L3), dedupe by node_id (L4), snapshot
  qname/kind at add time.
- **Anchor remove** — by node_id; removing an *unresolved* anchor is legal
  (the node is gone; the ref must still be removable).
- **Anchor move (transfer)** — one atomic operation: source may be dead
  (that's the re-anchor flow), target must resolve live; if the resolved
  target is already anchored, the move **degenerates to a remove** with a
  "merged" note. One commit, one system note, summary invalidated.
- **Update (PATCH)** — partial semantics: `None` = untouched, `""`/`[]` =
  deliberate clear; system notes on type/priority change only.
- **Move (status/rank)** — column validated against the live board; note
  appended only when the column actually changes.
- **Subtask edge add** — cycle check direction is subtle (08 spells it out
  with a worked example); existing-vs-inline create in one endpoint.
- **Delete** — unlink from every parent/blocker **first** (self-links make
  TerminusDB refuse deletes of referenced docs — that's a feature), then
  delete.
- **Schema migration** — new link fields with legacy `*_ids_json` read
  fallback; lazy upgrade on next save.

## Build sequence (each step ends demoable)

| Step | What | Done when |
|---|---|---|
| B1 | Backend: routes → query-param ids, drop `@cache` (08 §1–2) | HTTP test: create → move → patch → note round-trips with real ids; board GET carries no `Cache-Control: max-age` |
| B2 | Backend: schema self-links + migration (08 §3) | raw document shows `subtasks` links; legacy task loads |
| B3 | Backend: anchor algorithms + call rule + `anchors/move` (08 §4) | unit tests from 08's gate table pass |
| F1 | Frontend: theme.ts + api client rewrite + error toasts (09 §1–2) | board loads, a move sticks, a cycle shows its sentence |
| F2 | Board restyle: 5 columns, card anatomy, filter bar (09 §3, per 02) | side-by-side with mock passes |
| F3 | Detail panel rebuild (09 §4, per 03) | all nine sections round-trip |
| F4 | Modal mount at Dashboard + anchor pre-fill + picker (09 §5, per 07) | "New task here" works from canvas; call → target chip |
| F5 | Canvas/sidebar: badges, glow, popover, chips (09 §6, per 04) | two tasks on one node → amber everywhere; popover lists both |

Verification gates for the five original complaints: `../fixes/README.md`.
