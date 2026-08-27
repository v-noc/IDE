# 15 — Migration From Today's System

The current system is not thrown away. Most of it is already the right shape,
and the parts that change do so by addition rather than by replacement. This
file says exactly what stays, what changes, and what order makes sense to build.

No code and no schema statements. What matters here is which existing ideas map
onto which new ones, and where the sharp edges are.

---

## 1. What exists now

The shipped system has tasks with human keys, a subtask set (unordered), a
dependency list, soft anchors into the code graph with name snapshots, a notes
list for history, and the board.

```
   TASK today
     key · title · description · type · status · priority · labels · rank
     subtask_ids    a set, unordered     (will become parent_id on each child)
     blocked_by     a set               (renamed to depends_on)
     anchors        soft id + name snapshot
     notes          prose history        (becomes typed events)
```

Three decisions already made there are load bearing, and this design keeps all
three.

**Subtasks are tasks.** They are stored as real task-to-task links, not as a
separate type. The recursive model is a continuation of that decision, where
every task can have children.

**Pointers into the graph are soft.** A node id plus a snapshot of the name and
kind, so a deleted node produces a readable warning rather than a broken record.
The anchor field itself is going away, but this property of it is kept and every
link in this design follows the same rule.

**Hotness is computed.** Nothing stores whether a node is contested. The
derivation discipline in this design extends that to everything.

---

## 2. What maps onto what

| Today | In this design | Notes |
|---|---|---|
| Task | Task | Gains `document`, `node_links[]`, `parent_id`, `position`, `events[]` |
| `subtask_ids` set | `parent_id` on child + `position` | Moves from parent to child; gains order |
| `blocked_by` | `depends_on` | Same edge, clearer name, plus guards |
| `anchors[]` | `node_links[]` with mode `affects` | Field removed; every anchor converts |
| Notes | Events | Typed, machine-readable, same purpose |
| Board & columns | Board & columns | Unchanged, plus a level in the interface |
| Version entity | *removed* | Document and links move to Task |
| — | Single-parent tree | No DAG, no shared children, cascade delete |
| — | Soft delete | `deleted_at`, `deleted_batch_id`, undo via restore |
| — | Node links with modes | `read`, `create`, `affects`, `delete` — four, none vague |
| — | Conflict decisions | Two outcomes: `ordered` or `accepted` |

The critical lines: every child gets a `parent_id` field (not a set on parent),
and every task holds its document and links directly (no version indirection).

---

## 3. Migration steps

### Step 3.1 — Parent-child migration

Today: `TaskA.subtask_ids = {TaskB, TaskC}`
After: `TaskB.parent_id = TaskA; TaskC.parent_id = TaskA`

For each task's `subtask_ids` set:
```
FOR EACH task:
  FOR EACH child_id in subtask_ids:
    child_task = get(child_id)
    child_task.parent_id = task.id
    child_task.position = derive_lexorank_from(child_task.rank)
    write_event(child_task, "parent_changed", {from: null, to: task.id})
```

**Order derivation:** use each child's current `rank` on the board to derive
lexorank positions. This keeps the order stable and mostly sensible. The
interface shows on the parent task: "child order inherited from board ranks,
may need review."

### Step 3.2 — Report tasks with multiple parents

If a task appears in two parents' `subtask_ids` sets, it will conflict:

```
FOR EACH task with parent_id already set:
  IF another task also wants to set parent_id on it:
    report conflict:  "task VN-9 appears in both VN-3 and VN-7"
    show options:
      a) parent it under VN-3 only
      b) parent it under VN-7 only
      c) delete the VN-3 reference and create depends_on VN-3 → VN-9
         (meaning VN-3 depends on VN-9 being done)
```

Do not guess. A human chooses which parent is right, or converts to a dependency.

### Step 3.3 — Report forbidden dependencies

Check all existing `blocked_by` edges against the guard rule:

```
FOR EACH dependency edge A → B:
  IF B is an ancestor of A:
    report: "VN-11 depends on VN-3, but VN-11 is a child of VN-3 (deadlock)"
    action: human must remove the edge or restructure the tree
  IF B is a descendant of A:
    report: "VN-3 depends on VN-11, but VN-11 is a child of VN-3 (redundant)"
    action: system can drop this silently with a note, or human confirms
```

Do not delete silently. Report and let somebody decide.

### Step 3.4 — Rename and migrate dependencies

Rename the `blocked_by` field to `depends_on`. Keep both names on the API for
one release so no client breaks:

```
{ depends_on: [id1, id2],   // new name
  blocked_by: [id1, id2] }   // alias for backwards compatibility, one release only
```

### Step 3.5 — Migrate notes to events

Convert existing prose notes to typed events:

```
FOR EACH task note (text, at, origin, author):
  create_event(task, {
    type: "comment",
    payload: { text: text },
    at: at,
    origin: origin,
    author: author
  })
```

No information is lost. The rendering at display time produces the same text a
person sees today.

### Step 3.6 — Add soft-delete fields

Add to every task:
- `deleted_at` — timestamp, null if active
- `deleted_batch_id` — shared by tasks deleted together

Today, deleting is hard delete. After migration, deleting becomes soft delete.
A single undo restores the whole subtree via `deleted_batch_id`.

### Step 3.7 — Convert anchors to links

Every existing anchor becomes a node link:

```
FOR EACH task, FOR EACH anchor:
  create node_link(
    node_id  = anchor.node_id,      # unchanged
    qname    = anchor.qname,        # unchanged
    kind     = anchor.kind,         # unchanged
    mode     = "affects"
  )
  write_event(task, "link_added",
              {mode: "affects", qname: anchor.qname,
               note: "converted from anchor"})
drop the anchors[] field
```

The node id and the name snapshot carry over exactly. Only the mode is new, and
the event makes the change visible in each task's history rather than having
links appear from nowhere.

**Why `affects` and not `read`.** An anchor meant "this work is around here",
which in practice nearly always meant the work would change that code — that is
why people anchored it. `read` would understate it and quietly remove those
nodes from collision detection, which is the opposite of what the shipped hot
rule did. `affects` preserves the existing behaviour: two open tasks on one node
still produce a signal.

**Expect a burst of warnings, and check it before shipping.** Converted anchors
enter collision detection with a real mode, so pairs that used to show a mild
"hot" badge can now show a conflict. The status rule absorbs most of this — two
backlog tasks say nothing at all — but the pairs where both sides are in
progress will go loud. Run the conversion in a dry run first and count the
conflicts it would produce. If the number is large, that is information about
the codebase worth having before anybody sees amber everywhere.

**What is not attempted.** No migration tries to guess whether an anchor should
have been `read`, or whether it should have pointed at a function inside the
anchored class instead. Both would be guesses, and a wrong mode written by a
script is indistinguishable from one a person chose. People correct them as they
touch the tasks.

---

## 4. What to check before calling it done

```
every task has zero or one parent_id
no task is its own ancestor
no dependency points at an ancestor
no dependency cycle exists
every existing subtask appears under exactly one parent
deleting a task removes its whole subtree and nothing outside it
every anchor that existed before migration is now an affects link
the anchors[] field is gone, and no code reads it
two tasks adding different methods to one class do not collide
all existing notes converted to events, readable at display time
```

These are the invariants. Write them as tests — they are the normative spec.

---

## 5. Build order — P0 through P3

Each phase is useful alone, so the work can stop at any point without leaving
something half-built. **P1 is the proof**: plan a function → write it → parser
sees it → plan checks itself.

### Phase 0 — Foundation

```
████░░░░░░░░  Single parent + ordered children + document + typed events
```

**What to build:**

- Migrate `subtask_ids` → `parent_id + position` (Step 3.1–3.3)
- Add `document` field to tasks (was on version, now on task)
- Add `events[]` replacing `notes`, with typed events
- Add soft delete: `deleted_at`, `deleted_batch_id`
- Board level now shows `where parent_id = current_id` instead of active version children
- Fix all child reads to use parent_id index instead of version lookup

**What this alone gives:** A proper tree structure with one parent per task, no
orphans, atomic delete, and versioning via the document text. No graph linking
yet. This is usable but incomplete.

**Entry point for P1:** Plan and implement small tasks work fine. Coordination
at scale cannot work until nodes are linked.

### Phase 1 — Graph links (THE PROOF)

```
████████░░░░  Node links, modes, pending/fulfilled, verified
```

**What to build:**

- Add `node_links[]` to tasks with modes: `read`, `create`, `affects`, `delete`
- Convert every anchor to an `affects` link and drop `anchors[]` (Step 3.7)
- Enforce that `affects` names the node itself — adding a method writes a link
  on the function, not on the class
- Derive the location line from the nearest common container of a task's links
- Implement pending/fulfilled states for `create` links
- Implement binding: when parser produces a node matching (qname, kind),
  write a `verified` event with graph revision
- Index node links two ways: by node_id (for fulfilled) and by (qname, kind)
  (for pending)
- Add "Ghost nodes" render on canvas for pending creates
- Turn the anchor summary endpoint into the node work summary, reading links
  with their modes

**What this alone gives:** "waiting on code" warnings, verification that what
you planned was actually written, and the node-to-tasks lookup with modes. This
is where the design stops being a task board.

**This is the proof:** somebody plans `createComment()`, writes it, the parser
sees it, the plan turns green. Everything after this is refinement.

### Phase 2 — Level board and readiness

```
██████████░░  Board levels, guards, waiting-on-code, rollup
```

**What to build:**

- Board level: show children of one task, with breadcrumb
- Root level: show tasks where parent_id is null
- Implement ancestor/descendant guards on depends_on writes
- Compute `ready`, `blocked`, `waiting_on_code` on every read
- Rollup blocking: if a descendant is blocked, parent shows 🔴
- Tree view in sidebar with link badges
- Canvas badges updated for link modes

**What this alone gives:** The recursive model becomes navigable at scale. A
board with two hundred tasks is not crowded, it is nested.

### Phase 3 — Contested nodes and conflict decisions

```
████████████  Contested, conflict decisions (ordered, accepted)
```

**What to build:**

- Detect when two tasks have write modes on the same node
- Show contested markers on cards and canvas
- Allow human decisions: `ordered` (creates a dependency) or `accepted`
  (dismisses with reason)
- Suggestion: detect when a read link points to a node another task is
  rewriting
- Suggestion: detect when one task is creating what another is waiting to read

**What this alone gives:** Coordination features. These are last because they
need the most data to be useful.

---

## 6. Invariants that must hold afterwards

Write these as tests. They are the normative spec:

```
every task has zero or one parent
no task is its own ancestor (cycle detection on parent_id)
no dependency points at an ancestor or descendant
no dependency cycle exists
every existing subtask appears under exactly one parent
deleting a task removes its whole subtree atomically
soft delete restores whole subtree via deleted_batch_id
a create link bound to a real node turns "done" into "done, verified"
every anchor that existed before migration is now an affects link
the anchors[] field is gone, and no code reads it
two tasks adding different methods to one class do not collide
two backlog tasks affecting one node produce no warning
```

---

## 7. What to leave alone

**The parser, and every graph schema.** No node type gains a field pointing at
tasks. "Which tasks touch this node" stays a question asked from the work side,
using the link index.

**Hard links between tasks.** Task-to-task references stay real links for
referential integrity on children and dependencies.

**Soft pointers into the graph.** Node links stay soft, the way anchors were: an
id plus a name snapshot. A hard link would either block the parser's deletes or
break on rename. The anchor field goes; this property of it stays.

**The board.** Columns, flags, drag-and-drop, and ranks all stay. The level is
a view layered on top.

---

The final file, [16 — Open questions](16-open-questions.md), lists what this
design did not settle.
