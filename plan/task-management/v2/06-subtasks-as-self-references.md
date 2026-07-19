# v2 · 06 — Subtasks as TerminusDB self-references

## The problem with what shipped

`TaskSchema` (`core/model/schemas/task_schema.py`) stores its edges as
JSON-string blobs:

```python
subtask_ids_json: str = "[]"
blocked_by_ids_json: str = "[]"
```

To TerminusDB these are opaque strings. That forfeits everything the house
model already relies on elsewhere:

- **No referential integrity** — a blob happily holds the id of a deleted
  task; every read has to defensively filter (`if child_id in task_by_id`,
  `task_service.py:_enrich_task`) forever.
- **No graph queries** — closure, shared-parent counts, and cycle checks
  can never be pushed into WOQL; they must always load every task into
  Python.
- **Opaque diffs** — the versioning UI shows one changed string, not
  "edge VN-9 → VN-11 added". Task history riding commits (a v1 selling
  point) is unreadable for edges.
- **Off-pattern** — the codebase already does this correctly, including
  **self**-references: `class_children: Set["ClassSchema"]` on
  `ClassSchema` itself, `function_children: Set["FunctionSchema"]`,
  `documents: Set[DocumentSchema]` (`code_element_schema.py:28-32,119-127`).

## The TerminusDB way

Task→task edges become real link sets on the schema — the same
forward-reference syntax `ClassSchema` uses on itself:

```python
class TaskSchema(BaseSchema):
    key: str
    task_type: str
    status: str
    priority: str
    rank: str
    subtasks: Set["TaskSchema"]        # ← self-referencing links
    blocked_by: Set["TaskSchema"]      # ← same class, second edge kind
    labels_json: str = "[]"            # value data stays JSON (below)
    anchors_json: str = "[]"
    notes_json: str = "[]"
```

`TaskNode.subtask_ids: set[str]` / `blocked_by_ids: set[str]` stay as they
are — the pydantic layer keeps working with ids; only the schema mapping
changes. `from_pydantic` emits the id set as the link set (TerminusDB
accepts `{"@id": …}` refs / id strings); `to_pydantic` reads
`subtasks` / `blocked_by` refs back into the id sets (`from_raw_dict`
already tolerates both spellings — `tasks.py:50-52` reads
`subtask_ids_json` *or* `subtask_ids`; extend that fallback chain with the
link fields, which arrive as lists of `{"@id"}` dicts or id strings).

## The line: which fields are links, which stay JSON

| Field | Representation | Why |
|---|---|---|
| `subtasks` | **link set** `Set["TaskSchema"]` | Both endpoints are tasks; lifecycle fully owned by the task service — integrity is pure win |
| `blocked_by` | **link set** `Set["TaskSchema"]` | Same |
| `anchors` | **stays JSON** (soft refs + snapshot) | v1 decision 1 is still right: anchors point at code nodes that the **parser deletes at will** on reparse. A hard link would either block the parser's deletes or be refused — "unresolved anchor with a snapshot" is the feature, not a bug. Task→task = hard; task→node = soft. |
| `labels`, `notes` | **stay JSON** | Value objects, not documents; no integrity or query story — same pattern as `ConversationSchema.messages_json` |
| Board `columns` | stays JSON | Value objects on one singleton document |

## What the links buy immediately

1. **Delete integrity.** `delete_task` currently scans **every** task to
   scrub dangling ids (`task_service.py:232-252`). With links, TerminusDB
   refuses to delete a still-referenced task — the service unlinks parents
   first (it already has `delete_with_parent_cleanup(parent_field=…)` for
   exactly this shape) and the full-table scrub disappears.
2. **Honest commits.** An edge add/remove diffs as a link change on the
   task document — the commits view shows it.
3. **Query seams.** Shared-subtask detection (`parent count > 1`), the
   subtask closure, and eventually the anchor-summary hot rule can move
   into WOQL when boards grow — impossible with blobs. (v2 keeps these in
   the service; the point is the door opens.)

**Stays in the service regardless:** the DAG cycle check — TerminusDB
does not enforce acyclicity; `_validate_no_cycle` remains the guard, as
does closure dedupe.

## Migration

The feature has barely shipped, but tasks may exist on real branches:

- Keep `subtask_ids_json` / `blocked_by_ids_json` as **deprecated read
  fallbacks** in the schema for one release: `to_pydantic` prefers the
  link fields, falls back to the blobs when the links are empty and the
  blob isn't.
- `ensure_schema` bump: on first write after upgrade, tasks round-trip
  through `from_pydantic` and come out with real links (`_save_task`
  already rewrites the whole document). No offline migration script
  needed; a one-time "resave all tasks" maintenance call in
  `ensure_schema` makes it eager if wanted.
- Remove the blob fields once a resave has landed everywhere.

## Test gate

- Create parent + child → raw TerminusDB document for the parent contains
  a `subtasks` link (not a JSON string); commits view shows the edge.
- Delete a child that is still referenced → service unlinks parents first,
  then deletes; no dangling ids anywhere afterwards (assert by raw read,
  not via the defensive filter).
- Old-format task document (blob populated, links empty) loads correctly
  and is upgraded on next save.
- Cycle refusal still fires with the same sentence (service guard
  untouched).
