# 01 — Data Model

What a task **is** in TerminusDB terms, where it lives, and the three laws the
schema enforces: soft anchors, guarded DAG, per-column done-ness.

## Placement: project db, current branch

Tasks are project data, so they live where documents, conversations, and logs
already live: the project's own TerminusDB database, on the working branch,
through the same `scoped_client` (`app/db/scoped_client.py` applies
db/branch/ref). Nothing new in the db layer.

Consequences, stated honestly:

- Branch experiments see their own task state; promoting a branch merges task
  changes with the same machinery as graph changes.
- The UoW `compare_to` path (see `document_routes.py`) extends to tasks later
  ("what did this branch do to the board") — a seam, not v1.
- **Seam — branch-agnostic tasks:** if real usage shows tasks should survive
  branch switches unchanged (Jira semantics), the escape hatch is moving the
  task region to a fixed branch read through a second scoped client. The
  schema below doesn't change either way; only the client scoping does. Do
  not build this until someone actually hits it.

## Schemas (`app/core/model/schemas/task_schema.py`)

House pattern: `BaseSchema` subclasses (TerminusDB `DocumentTemplate`) with
paired pydantic models in `app/core/model/` (`from_pydantic` / `to_pydantic`),
same as `code_element_schema.py`.

```python
class TaskAnchorSchema(DocumentTemplate):        # subdocument of TaskSchema
    _subdocument = []
    node_id: str          # "FunctionSchema/abc123" — soft ref, NOT a typed link
    qname: str            # "main.dd" — snapshot at anchor time, shown to users
    kind: str             # "function" | "class" | "file" | "folder" | "call"

class TaskSchema(BaseSchema):                    # name = title, description = markdown
    key: str                        # "VN-12" — human key, unique per project
    task_type: str                  # "epic" | "task" | "bug" | "improvement"
    status: str                     # BoardColumn id
    priority: str                   # "none" | "low" | "medium" | "high" | "urgent"
    labels: Set[str]                # free-form chips
    rank: str                       # LexoRank within (board, status)
    subtasks: Set["TaskSchema"]     # DAG edges, typed refs (task↔task is safe)
    blocked_by: Set["TaskSchema"]   # dependency edges, typed refs
    anchors: List[TaskAnchorSchema] # soft refs into the code graph
    notes: List["TaskNoteSchema"]   # activity entries (subdocuments: text, at, origin)

class BoardColumnSchema(DocumentTemplate):       # subdocument of BoardSchema
    _subdocument = []
    id: str               # "backlog" | "todo" | ... (stable, never renamed)
    title: str            # user-editable display name
    color: str
    is_done: bool         # done-ness — everything derives from this
    is_backlog: bool      # the pen — kanban never renders it; List view owns it

class BoardSchema(BaseSchema):
    columns: List[BoardColumnSchema]
    task_counter: int     # mints VN-<n>
```

Notes on the shape:

- **`task_type`/`priority` as strings, not `EnumTemplate`.** The folder-schema
  precedent (`is_root: str` to dodge the xsd:boolean issue) says this codebase
  prefers plain strings validated in pydantic. Validation lives in the
  pydantic models; the db stores strings.
- **`anchors` is a list of subdocuments** with set semantics: **at most one
  anchor per `node_id`** (the service dedupes; add-existing is a no-op). Order
  is kept for display only — first anchor = the primary one shown on compact
  cards. All anchor operations are keyed by `node_id`, never by list index;
  that is what makes every linking surface a safe toggle (02).
- **`notes` replaces a full activity/event system.** v1 activity = system
  sentences appended by `TaskService` ("moved to In progress", "anchor became
  unresolved") plus user notes. Same list, `origin: "system" | "user"`.

## The anchor law: soft refs only

`CallSchema.target_function` is a typed link, and the codebase already carries
the scar tissue of typed links into a graph the parser rewrites (`@oneOf`
workaround, `/None` legacy ids — see `_scope_id_usable`). Anchors deliberately
are **not** typed links:

- A typed link to a deleted node breaks referential integrity or forces
  cascade behavior the parser would have to know about. A string survives.
- The dangling string **is the feature**: "unresolved anchor" = this string no
  longer names a live document (02 derives it; nothing stores it).
- The snapshot (`qname`, `kind`) is what the UI renders when the node is gone
  and what the re-anchor search uses as its query seed.

Symmetrically: **no `tasks` field is added to any node schema.** The parser,
`GroupService`, migrations, and every existing write path remain untouched.
"Tasks on this node" is a task-side query (03).

## The DAG law

`subtasks` and `blocked_by` are plain edge sets; multiple parents are legal by
construction (a `Set` on each parent). What must be guarded:

- **Cycle check on every edge add** (subtask *and* blocked_by, independently).
  Service-side traversal over the task closure — task graphs are small
  (hundreds, not millions); a BFS in `TaskService` beats a WOQL path query in
  clarity and gives the refusal sentence for free:
  `"VN-11 already contains VN-9 through VN-12 — adding this edge would create a cycle."`
- **Self-edges refused**, same sentence machinery.
- **Closure counting dedupes.** `open_subtask_count`, progress `2/5`, and the
  hot computation (02) walk the closure with a visited set. A task reachable
  through two parents counts once.
- **Shared detection is a count, not a flag:** a subtask row shows `⑂ shared`
  when `len(parents) > 1`, computed by the service when it assembles the
  detail view. Never stored.

Deletion semantics: deleting a task removes it from every parent's `subtasks`
and every dependent's `blocked_by` (one commit batch). Subtasks are **not**
cascade-deleted — they may have other parents; orphans simply become
top-level tasks.

## Ordering: LexoRank strings

`rank` is a base-36 midpoint string, meaningful only within (board, status).
Move = compute midpoint between neighbors client-side, server re-validates and
rebalances the column on midpoint exhaustion (rare; log when it happens).
One field update per drag — no renumbering writes, which keeps drag-and-drop
a single small commit.

## Column semantics: `is_done` and `is_backlog`

Two flags, both on the column, both driving derived values — status stays a
plain column id and tasks never carry semantic booleans themselves:

| Derived value | Rule |
|---|---|
| open task | `status` column has `is_done == False` — **backlog tasks are open** (a parked task anchored to a node is still converging work; hot counts include it. An "active-only" hotness toggle is a seam, not v1) |
| progress `2/5` | done = closure members in `is_done` columns, deduped |
| blocked | any `blocked_by` task open |
| hot node (02) | counts **open** tasks only |
| on the kanban (04) | column has `is_backlog == False` |
| List view sections (04) | Active = non-backlog columns (grouped by status) · Backlog = the `is_backlog` column, rank-ordered |

Backlog laws:

- **Exactly one backlog column** per board, created by the bootstrap,
  protected: it can be renamed/recolored but not deleted and not un-flagged
  in v1 (`PATCH /tasks/board` refuses with a sentence, 03). Zero backlog
  columns would strand the List view's bottom section; two is ambiguity
  nobody asked for.
- Moving a task to/from backlog is an ordinary `move` (status + rank) — no
  special endpoint, no special state. The board simply never paints that
  column; the List view's divide is where the crossing happens (04).
- `is_backlog` and `is_done` are mutually exclusive (validator).

Column ids are stable; titles are what users rename. Deleting a non-backlog
column requires naming a destination column for its tasks (service refuses
otherwise).

## Human keys

`key` = `VN-<n>` from `BoardSchema.task_counter`, minted in `TaskService.create`
inside the same commit as the task itself. Keys are never reused; the counter
only grows. Document `_id` stays a random key (`TaskSchema/<uuid>`), matching
`RandomKey` house default.

## Pydantic models (`app/core/model/tasks.py`)

`TaskNode`, `TaskAnchor`, `BoardNode`, `BoardColumn` mirroring the wire shapes
of the mock's TypeScript (`Task`, `TaskAnchor`, `Board`, `BoardColumn`), with:

- `from_raw_dict` / schema `from_pydantic`/`to_pydantic` pairs, house-style.
- API responses extend the stored shape with derived fields:
  `is_resolved` per anchor, `blocked`, `subtask_progress`, `shared_parents`
  per subtask, `blocks` (reverse of `blocked_by`). Derived fields never
  round-trip back into writes.
