# The Rules

This is the normative artifact for the planning system. Everything else in this
folder is rationale. If this file and another file disagree, **this file wins**.

---

## 1. The three stored edges

```
   child ──parent_id────────────────►  task         containment, one parent only
   task  ──depends_on──────────────►  task         ordering
   task  ──node_link (with mode)───►  graph node   code involvement
```

Nothing else is stored as a relationship. There is no `children[]` array on the
parent, no reverse dependency edge, and no stored record that a collision
exists.

---

## 2. The Task

```
STORED
  id · key · title · description
  type · status · priority · labels
  rank                  board column position (lexorank)
  parent_id             task id, or null for top-level
  position              sibling order (lexorank)
  document              markdown
  node_links[]          mode: read | create | affects | delete
  depends_on[]          task ids
  verified_by_tests[]   test node references, optional
  events[]              typed
  created_at · updated_at
  deleted_at            null when live
  deleted_batch_id      shared by everything deleted in one operation
```

`rank` and `position` are different fields. `rank` orders a card within a board
column. `position` orders a task among its siblings. Neither may be overloaded
to do the other's job.

---

## 3. Everything derived

Never stored. Computed on every read.

| Value | Computed from |
|---|---|
| `children` | tasks whose `parent_id` is this id, ordered by `position` |
| `breadcrumb` | walking up `parent_id` to the root |
| `depth` | length of that walk |
| `blocked` | any task in `depends_on` is not done |
| `blocks` | reverse view of other tasks' `depends_on` |
| `waiting_on_code` | a `read`/`affects`/`delete` link points at a node that does not exist |
| `ready` | not blocked and not waiting on code |
| `progress` | finished direct children over total |
| `blocked_below` | any descendant is blocked |
| `effective_links` | own links merged with every descendant's links |
| link state | `live` · `pending` · `fulfilled` · `missing` · `unresolved` |
| `verified` | a `verified` event exists for this task |
| `contested` | two or more open tasks hold write-mode links on one node |

**Deleted for good:** `parents` (plural), `all_parents`, `is_shared`,
`is_orphaned`. The orphan concept does not exist in this model.

---

## 4. The one evaluation function

Every derived value above comes from a single pure function:

```
evaluate(task, snapshot) -> {
    blocked, waiting_on_code, ready, verified,
    contested, progress, blocked_below
}
```

`snapshot` is an explicit input carrying the statuses of dependency targets, the
set of existing node qnames and ids, and the write-mode links of other open
tasks. **No database access inside the function.** The API, the UI payloads, the
agent, and the tests all call this same function.

---

## 5. Three storage categories

| Category | Rule |
|---|---|
| **Stored truth** | Written by a person or an agent. The three edges plus task fields. |
| **Regenerable index** | Materialized, single writer, rebuilt from source, never hand-edited. Safe to persist. |
| **Computed on read** | Everything in §3. |

Whole-project queries — contested nodes across the project, "what is ready
anywhere" — belong in the middle category. They do not fit the per-level
batching model and are the first thing to break at scale.

---

## 6. The guards

Every refusal returns a sentence naming what was wrong and what to do instead,
never an error code.

### On `add depends_on`

| Case | Verdict |
|---|---|
| target is an ancestor of the task | **refuse** — true deadlock, name the path |
| target is a descendant of the task | **drop silently**, write an event — redundant, not a trap |
| the edge would close a cycle | **refuse**, name the path |

### On `set parent_id`

| Case | Verdict |
|---|---|
| new parent is a descendant of the task | **refuse** — containment cycle |
| task depends on the new parent | **refuse**, name the edge to remove |
| new parent depends on the task | **drop that dependency**, write an event |

Both write paths are guarded. Guarding only the dependency write leaves a hole:
add `A depends_on B`, then make A a child of B, and the deadlock arrives through
the back door.

Ancestry is a walk up `parent_id`. Bound it with a depth ceiling so malformed
data cannot spin.

---

## 7. Delete

Deleting a task deletes its whole subtree. There is no orphan rescue and no
reparenting to root.

The delete is **soft**: set `deleted_at` and a shared `deleted_batch_id` on
every task in the subtree. One undo restores the whole batch. Every read filters
`deleted_at is null` by default.

Before confirming, find dependencies that cross the delete boundary and show
them:

```
   Deleting VN-3 removes 7 tasks.
   2 tasks outside this subtree depend on tasks inside it:
      VN-9  ──depends_on──►  VN-5
      VN-14 ──depends_on──►  VN-6
   These tasks will no longer be blocked.
```

On confirm, remove those inbound edges and write an event on each affected
outside task.

---

## 8. Links

A task points at code in exactly one way: `node_links[]`. There is no vague
mode — every link makes a claim the graph can check.

| Mode | Meaning |
|---|---|
| `read` | Must be read to do the work. Will not change. |
| `affects` | This node's own body or signature changes. |
| `create` | Does not exist yet. This work makes it. |
| `delete` | Exists. This work removes it. |

A task may link to any number of nodes. There is no primary link.

`create`, `affects`, and `delete` are restricted to **folder, file, class,
function**. A `call` may only be `read`.

### `affects` means the node itself, never its contents

> Changes to a node's **contents** are derived from the links on those contents.
> They are never typed on the container.

Adding a method to a class is **one** link:

```
   TYPED
     create   function  Comment.validate     container: class Comment

   DERIVED
     touches  class Comment      it contains the new function
     touches  file  models.py    it contains Comment
```

Write `affects class Comment` only if the class itself also changes — a new
field, a changed base class, a decorator.

Without this rule, two tasks each adding a *different* method to `Comment` would
both type "affects class Comment" and be reported as colliding. They do not
collide, and every class in the codebase would become a false alarm.

**Limit:** derived containment never verifies anything. Only explicit links have
states. A class is not verified because a function inside it appeared.

### Location is derived, not stored

Take the nearest container holding every linked node. If it is specific (a file
or a class), show it as the location. If it is too broad (a top folder, or the
repo), show the list of linked nodes instead. Display rule only — nothing stored
changes.

A `create` link's identity is **(qname, kind)**, not a node id:

```
   node_id      empty until fulfilled
   qname        app.services.createComment
   kind         function
   container    node id + name snapshot of the file or class it goes in
   mode         create
   state        derived: pending | fulfilled
```

The link index is keyed **two ways** — by `node_id` for resolved links, by
`qname` for unresolved ones. A node lookup checks both.

**Never let a user free-text a full qname.** Compose it: pick a container node,
type the leaf name, pick a kind, derive the qname. A typo otherwise leaves a
link pending forever, which looks identical to work never being done.

**Binding:** a pending create fulfils when a node matches **both** qname and
kind. Wrong kind at the right qname does not fulfil — it shows as a mismatch.
Rebinds are **suggested, never applied silently**.

| Situation | Behaviour |
|---|---|
| Node already exists when a `create` link is written | Warn: "already exists — did you mean affects?" |
| Two open tasks plan the same qname | Duplicate warning, **not** a dependency |
| Container does not exist either | Fine. Both creates fulfil together |
| Node appears with the wrong kind | Do not fulfil. Show a mismatch |

---

## 9. Verification

Verification is a **decision recorded at a point in time**, not a value
recomputed forever.

```
   event: { type: "verified",
            payload: { link_qnames: [...], node_ids: [...], graph_revision },
            at, origin, author }
```

A task shows "done, verified" if the event exists. If a verified link later goes
unresolved, show "verified at `<revision>`, node since removed" — a note, not a
reversal.

`verified_by_tests[]` is the second source. It covers the rewritten-in-place
hole, and it gives verification to work with no graph trace at all
(documentation, config, conversations).

---

## 10. Events

Typed, never prose. The English sentence is rendered from `type` + `payload` at
display time and is never stored.

```
   TaskEvent = {
     type: "status_changed" | "link_added" | "dependency_added" |
           "task_created" | "parent_changed" | "deleted" | "restored" |
           "verified" | "conflict_decided" | "comment"
     payload: dict
     at: datetime
     origin: "system" | "user" | "agent"
     author: str
   }
```

A free-text human comment is `type: "comment"` with `payload: {text}`.

---

## 11. Conflicts

A collision is **computed, never stored**.

### Severity comes from task status, not from the link

There is no `source` field and no `typed / inferred` flag on a link. The
existing `status` field already carries the information.

| Situation | Warning |
|---|---|
| Two ready or in-progress tasks affect the same node | **conflict** — loud |
| One ready, one draft | **watch** — quiet |
| Two drafts | nothing |

A draft task's links are ideas; a ready task's links are claims. Promoting a
task out of draft is the moment its plan becomes a claim. "Draft" means the
backlog column — the one carrying `is_backlog` — so no new state is introduced.

**Known gap, accepted:** a task left in draft forever warns nobody. The answer
is a housekeeping list — *draft tasks with links, unchanged for N days* — not a
new field.

### Only the human decision is stored

It has exactly two outcomes:

- **`ordered`** — writes a real `depends_on` edge. The decision records why.
- **`accepted`** — dismissed with a reason. Stays dismissed unless links change.

`resolved` and `delegated` were cut. They were records with no mechanism behind
them.

---

## 12. The invariants

These are the normative spec. Write them as tests.

```
every task has zero or one parent
no task is its own ancestor
no dependency points at an ancestor
no dependency cycle exists
every existing subtask appears under exactly one parent
deleting a task removes its whole subtree and nothing outside it
a create link bound to a real node turns "done" into "done, verified"
two tasks adding different methods to one class do not collide
two backlog tasks affecting one node produce no warning
```

---

## 13. What not to do

**Do not leave a seam for versions to come back.** If alternatives matter later,
the answer in this model is a section in the document, or a separate proposal
task whose children are moved under the real task when accepted.

**Do not store any derived value.** No `is_blocked` column, no cached progress
count, no conflict table. A wrong stored value is undetectable; a slow
computation is merely slow.

**Do not hold both `parent_id` and `children[]`.** Two copies of one fact will
drift.
