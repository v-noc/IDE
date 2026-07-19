# v2 · 08 — Backend Implementation Spec

Files touched: `api/v1/task_routes.py`, `core/services/task_service.py`,
`core/model/schemas/task_schema.py`, `core/model/tasks.py`. Everything else
(repos, DI, socket manager) already exists — use it, don't rebuild it.
Follow the sections in order; each has a test gate.

## §1 Routes — ids move to query params (fixes the 404s, L7)

Task ids are `TaskSchema/{uuid}` — a `/` inside a path segment never
matches `/{task_id}`. Rewrite `task_routes.py` so **no task id is ever a
path segment**. New table (prefix `/tasks` unchanged):

| Method & path | Query | Body | → service |
|---|---|---|---|
| `GET  /board` | — | — | `get_board_payload()` |
| `GET  /anchor-summary` | — | — | `anchor_summary()` |
| `GET  /re-anchor-candidates` | `qname`, `kind?` | — | unchanged |
| `GET  /suggest-dependencies` | `node_id` | — | unchanged |
| `POST /` | — | CreateTaskRequest | `create_task(...)` |
| `PATCH /` | `task_id` | UpdateTaskRequest | `update_task(...)` |
| `POST /move` | `task_id` | `{status, rank}` | `move_task(...)` |
| `DELETE /` | `task_id` | — | `delete_task(...)` |
| `POST /subtasks` | `task_id` | `{child_id?}` or inline fields | `add_subtask(...)` |
| `DELETE /subtasks` | `task_id`, `child_id` | — | `remove_subtask(...)` |
| `POST /blocked-by` | `task_id` | `{blocker_id}` | `add_blocked_by(...)` |
| `DELETE /blocked-by` | `task_id`, `blocker_id` | — | `remove_blocked_by(...)` |
| `POST /anchors` | `task_id` | `{node_id}` | `add_anchor(...)` |
| `DELETE /anchors` | `task_id`, `node_id` | — | `remove_anchor(...)` — **by node_id, not index** |
| `POST /anchors/move` | `task_id` | `{from_node_id, to_node_id}` | `move_anchor(...)` — **new** |
| `POST /notes` | `task_id` | `{text}` | `add_note(...)` |
| `PATCH /board-columns` | — | `{columns[]}` | `update_board(...)` (renamed from `PATCH /board` so it can't collide with `GET /board`) |

Declare query params as `task_id: str = Query(...)`. Delete the routes
`DELETE /{task_id}/anchors/{index}` and
`POST /{task_id}/anchors/{index}/re-anchor` — index addressing is gone
(L4); re-anchor IS `anchors/move` with a dead source.

**Gate:** an HTTP test (`tests/…/test_task_routes.py`, use the app test
client) that creates a task, then hits every route above with the real
`TaskSchema/…` id and asserts non-404.

## §2 Caching — delete it (L8)

In `task_routes.py`: remove both `@cache(expire=DEFAULT_TTL)` decorators
and the `fastapi_cache` / `DEFAULT_TTL` imports. Do **not** replace with a
smaller TTL — any `@cache` here re-adds the browser `max-age` poison
(`../fixes/01`). Freshness = react-query invalidation + the socket emits
already in `_emit_changed` (keep those).

**Gate:** `GET /board` response headers contain no `Cache-Control`.

## §3 Schema — self-referencing links + migration (L2)

In `task_schema.py`:

```python
class TaskSchema(BaseSchema):
    key: str
    task_type: str
    status: str
    priority: str
    rank: str
    subtasks: Set["TaskSchema"]      # NEW — real links, like ClassSchema.class_children
    blocked_by: Set["TaskSchema"]    # NEW
    labels_json: str = "[]"
    anchors_json: str = "[]"
    notes_json: str = "[]"
    subtask_ids_json: str = "[]"     # DEPRECATED — read-fallback only
    blocked_by_ids_json: str = "[]"  # DEPRECATED — read-fallback only
```

- `from_pydantic`: emit `subtasks` / `blocked_by` from
  `node.subtask_ids` / `node.blocked_by_ids` (the terminusdb client
  accepts id strings / `{"@id": …}` refs — copy whatever
  `code_element_schema.py` does for `class_children`). Keep writing the
  deprecated json fields too during the transition (harmless, aids
  rollback), or write `"[]"` — either is fine, but be consistent.
- `to_pydantic` / `TaskNode.from_raw_dict` (`tasks.py`): read links first,
  fall back to blobs: link values arrive as a list of id strings **or**
  `{"@id": ...}` dicts — normalize both. Only if the link set is empty AND
  the blob is non-empty, use the blob (legacy row).
- `TaskRepo.ensure_schema()` must push the updated schema class (it
  already handles schema creation — verify it also handles *update*; if it
  only creates-when-missing, add an explicit schema replace for
  TaskSchema).
- **Lazy migration**: `_save_task` rewrites the whole document, so any
  legacy task upgrades on its first write. No offline script.

**Gate:** unit test — build a TaskNode with 2 subtask ids, round-trip
through `from_pydantic` → raw dict → `to_pydantic`, ids survive; a raw
dict with only `subtask_ids_json` populated also loads.

## §4 Anchor algorithms (L1, L3, L4 — the tricky core, do not improvise)

### §4.1 `_snapshot_anchor(node_id) -> TaskAnchor` (rewrite)

```
1. raw = client.get_document(node_id)          # fails → 422 "…does not exist on this branch — pick a live node."
2. if node_id startswith "CallSchema/":        # the call rule, L3
     target = raw.get("target_function") or raw.get("target_class")
     if not target: 422 "This call's target no longer exists on this branch — anchor the function or class directly."
     target_id = target if isinstance(target, str) else target["@id"]
     return _snapshot_anchor(target_id)        # recurse once; targets are never calls
3. kind from schema prefix {Function→function, Class→class, File→file, Folder→folder}
   ("call" is NOT in this map anymore — unreachable after step 2)
4. qname = raw.get("qname") or raw.get("name") or node_id
5. return TaskAnchor(node_id=node_id, qname=qname, kind=kind)
```

### §4.2 `add_anchor(task_id, node_id)` — idempotent

```
1. task = _get_task_or_raise(task_id)
2. anchor = _snapshot_anchor(node_id)              # resolves calls → anchor.node_id may differ from input!
3. if any(a.node_id == anchor.node_id for a in task.anchors): return enriched(task)   # NO-OP, no note, no save
4. task.anchors.append(anchor); touch updated_at
5. append system note f"anchored to {anchor.qname}"
6. _save_task; _emit_changed(summary=True); return enriched
```

Step 3 is what makes double-clicks and two-call-sites-same-function safe.

### §4.3 `remove_anchor(task_id, node_id)` — idempotent, works on dead refs

```
1. task = _get_task_or_raise(task_id)
2. before = len(task.anchors)
3. task.anchors = [a for a in task.anchors if a.node_id != node_id]   # NO existence check on the node —
                                                                       # removing an unresolved anchor must work
4. if unchanged: return enriched            # NO-OP
5. touch, note f"unlinked {qname}", save, emit(summary=True)
```

Do NOT call `_snapshot_anchor` here — the node may be gone; that's fine.

### §4.4 `move_anchor(task_id, from_node_id, to_node_id)` — transfer, one commit

This one endpoint serves plain transfer AND the re-anchor repair flow
(re-anchor = move whose source is dead). Atomic: one save, one note.

```
1. task = _get_task_or_raise(task_id)
2. src = next((a for a in task.anchors if a.node_id == from_node_id), None)
   if src is None: 404 f"{task.key} has no anchor on {from_node_id}"
3. new = _snapshot_anchor(to_node_id)        # target must resolve live; calls resolve (L3);
                                             # source is NEVER validated — it may be dead
4. if any(a.node_id == new.node_id for a in task.anchors if a is not src):
     # target already anchored → move degenerates to a remove-with-merge
     task.anchors.remove(src)
     note = f"anchor {src.qname} merged into {new.qname}"
   else:
     task.anchors[task.anchors.index(src)] = new    # replace IN PLACE (keeps position)
     note = f"re-anchored {src.qname} → {new.qname}"
5. touch, append system note, ONE _save_task, _emit_changed(summary=True), return enriched
```

Delete the old `re_anchor(index)` service method entirely.

## §5 Task lifecycle operations

### §5.1 `update_task` (PATCH semantics)

`None` = leave untouched; empty string/list = deliberate clear. Only
type/priority changes append system notes (existing behavior — keep).
Reject empty-after-strip titles: 422 `"A task needs a title."`.

### §5.2 `move_task(task_id, status, rank)`

Keep existing logic (validate column against live board, note only when
column changed). One addition: after PATCHing, if `rank` collides with
another task in the column (exact string equal), re-mint with
`mid_rank(rank, next_rank)` server-side — prevents two clients dropping on
the same midpoint from freezing the order.

### §5.3 `add_subtask` — cycle check, worked example (L6)

Edge to add: parent → child. The cycle exists iff **parent is reachable
FROM child** via subtask links. Direction matters; get it wrong and legal
links are refused while cycles pass:

```
VN-9 → VN-11 exists.  Request: add VN-11 → VN-9.
reachable_from(VN-9) via subtasks = {VN-9, VN-11}?  start at VN-9? NO —
start at the CHILD of the new edge: reachable_from(VN-9) … 
   new edge parent = VN-11, child = VN-9
   walk subtask links from VN-9: {VN-11}  → contains VN-11 (the parent) → CYCLE, refuse:
   "VN-11 already contains VN-9 through the subtask graph — adding this edge would create a cycle."
```

The shipped `_path_exists(start=to_id, target=from_id, field)` implements
exactly this — keep it, and keep the self-link guard. Same shape for
`blocked_by` (field swap). `add_subtask` supports `child_id` (link
existing) or inline create (title/type/…) — inline path creates first,
then links, and if the link is refused the created task **still exists**
(acceptable; note it in the response error so the UI can say so).

### §5.4 `delete_task` — unlink first, then delete (self-link ordering)

With real links (L2), TerminusDB may refuse deleting a referenced
document — rely on that, don't fight it:

```
1. load all tasks once
2. for every task T where task_id ∈ T.subtask_ids or T.blocked_by_ids:
     discard the ref, touch updated_at, collect
3. bulk-update the collected tasks (ONE update_nodes call, one commit msg)
4. delete the task document
5. emit(summary=True)
```

(The shipped code already has this scan — after L2 it becomes mandatory
correctness, not defensive cleanup. Keep the bulk update, never N saves.)

### §5.5 `create_task`

Keep existing flow (mint `VN-n` from the board counter — save board
before task so a failed create can't reuse a key; rank at column top;
initial anchors through `_snapshot_anchor` so **the call rule applies at
create too**; optional `subtask_of` linking with cycle check).

## §6 Reads

- `get_board_payload` / `anchor_summary` / enrichment: unchanged logic,
  now reading link-backed id sets. `blocks` must be enriched like
  `blocked_by` (id/key/title/status) — the panel's DEPENDENCIES section
  needs it ([03](03-detail-panel.md) §7).
- `_resolve_anchor_ids` currently does one `get_document` per node —
  fine at v2 scale; leave a `# TODO batch via WOQL when boards grow`
  marker, do not build it now.

## §7 Test gates (write these, in `tests/unit/service` + HTTP)

| Test | Asserts |
|---|---|
| route smoke | §1 gate — every route reachable with real ids |
| no-cache | §2 gate |
| schema round-trip + legacy fallback | §3 gate |
| call resolution | `add_anchor(call_id)` anchors the target function; dangling call → 422 with the exact sentence |
| anchor idempotency | add same node twice → 1 anchor, 1 note; remove absent → no-op; two call sites of one fn → 1 anchor |
| move_anchor | plain move replaces in place + note; dead source works; target-already-anchored degenerates to remove with "merged" note; single commit (assert one updated_at bump) |
| cycle | §5.3 example verbatim, both edge kinds, self-link |
| delete | referenced child: parents unlinked in one bulk update, then deleted; no dangling ids on any survivor |
| rank collision | two moves to same midpoint → distinct ranks |
