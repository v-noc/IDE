# 03 — Data Model

This file lists every field of every entity. It is written as tables rather
than as code, because the point is to agree on what information exists and who
owns it, not to fix a storage format.

Two words matter more than the rest. **Stored** means a person or an agent
wrote it and the system keeps it. **Derived** means nobody wrote it and the
system works it out on every read. That split is the most important thing in
the file, because a derived value that gets stored by accident becomes a value
that is silently wrong.

```
   ENTITIES
   ────────
   Task                 the only work object
     ├── Version        one approach, at least one per task
     │     ├── Child reference   ordered pointer to another task
     │     └── Node link         pointer to a graph node, with a mode
     ├── Anchor         pointer to a graph node, mode "about"
     └── Note           one line of history

   Conflict decision    what a human decided about a collision
   Board                columns, unchanged from today
```

---

## Task

The task is the unit of work, the unit of display, and the unit of dependency.

### Stored fields

| Field | What it holds | Notes |
|---|---|---|
| `id` | The internal identifier | Never shown to people |
| `key` | The human key, such as `VN-9` | Flat, never reused, explained below |
| `title` | One line | What the card shows |
| `description` | One short paragraph | For scanning. Plain text or light markdown |
| `type` | `epic`, `task`, `bug`, or `improvement` | A label for filtering, not structure |
| `status` | The id of a board column | Unchanged from today |
| `priority` | `none`, `low`, `medium`, `high`, `urgent` | Unchanged from today |
| `labels` | A set of free text chips | Unchanged from today |
| `rank` | Position within its column | Ordering for drag and drop, unchanged |
| `anchors` | List of anchors | Where the work lives, roughly |
| `depends_on` | Set of task references | The only hand written ordering edge |
| `versions` | List of versions, at least one | The approaches |
| `active_version_id` | Which version is in effect | Exactly one, always set |
| `notes` | List of notes | History, human and system |
| `created_by` | A person, or an agent run | |
| `created_at`, `updated_at` | Timestamps | |

### Derived values

| Value | How it is worked out |
|---|---|
| `parents` | Every task whose **active** version refers to this one |
| `all_parents` | Every task any of whose versions refers to this one |
| `is_shared` | More than one active version refers to it |
| `is_orphaned` | No active version refers to it, and it is not a root |
| `blocked` | Something in `depends_on` is not finished |
| `blocks` | The reverse view of other tasks' `depends_on` |
| `waiting_on_code` | A `read`, `modify`, or `delete` link points at a node that does not exist |
| `ready` | Not blocked and not waiting on code |
| `progress` | Finished children of the active version, over total, counted without duplicates |
| `depth`, `path` | Distance from the nearest root, and the breadcrumb |
| `effective_links` | Its own links plus every descendant's links, merged |
| `verified` | Every `create` link now points at a node that really exists |
| `contested_nodes` | Nodes where this task and another open task both intend to write |

### Why the key is flat

A hierarchical key such as `VN-3.2.1` reads beautifully and breaks the first
time somebody moves a task to a different parent. Either the key changes, which
breaks every link and every mention in chat, or the key stays and now lies
about where the task sits.

A flat key never lies, because it never claims to describe position. Position
is shown by a breadcrumb, which is always current.

```
   FLAT KEY                            HIERARCHICAL KEY
   ────────                            ────────────────
   VN-42                               VN-3.2.1
   ▸ Comments ▸ Model ▸ VN-42          move it to another parent and the key
   the path is shown live              either changes or starts lying
```

**Tradeoff.** A flat key tells you nothing on its own, so somebody reading a
key in a chat message has to click it to learn where it lives. That is
accepted, because keys are identifiers and breadcrumbs are locations, and
mixing those two jobs is exactly what causes the breakage.

### Fields that were deliberately not added

| Not a field | Why |
|---|---|
| `parent_id` | A task can have several parents. One field would either lie or forbid sharing. Parenthood is derived |
| `is_blocked` | Changes when other people finish their work. Derived |
| `progress_count` | Changes when any child changes. Derived |
| `is_subtask` | There is no such type. Depth is derived |
| `estimate` | Postponed on purpose. Estimation is a feature with its own opinions, and nothing here needs it |
| `assignee` | Also postponed, and listed in [16](16-open-questions.md) |

---

## Version

A version is one answer to "how are we going to do this?". Every task has at
least one, and exactly one is active.

### Stored fields

| Field | What it holds | Notes |
|---|---|---|
| `id` | Internal identifier | |
| `name` | Short label, such as "Separate Comment class" | Only shown when a task has more than one version |
| `summary` | One or two sentences describing the approach | Used when comparing versions |
| `document` | The long write-up, in markdown | The main body of thinking |
| `children` | Ordered list of child references | See below |
| `node_links` | Links into the graph, each with a mode | Becomes the Context and Affects lists |
| `state` | `draft`, `active`, `superseded`, or `discarded` | Only one may be active |
| `derived_from` | The version this was copied from, if any | Tells a revision apart from a fresh alternative |
| `created_by` | A person, or an agent run | Matters for review |
| `created_at`, `activated_at`, `retired_at` | Timestamps | |

### Derived values

| Value | How it is worked out |
|---|---|
| `is_active` | The task's `active_version_id` points at it |
| `child_progress` | Finished children over total |
| `pending_creates` | `create` links whose node does not exist yet |
| `fulfilled_creates` | `create` links whose node now exists |
| `unresolved_links` | Links whose node id has disappeared from the graph |

### Why `state` is stored even though `is_active` is derived

`is_active` comes from the task's pointer, so there is one source of truth about
which version is in effect. The other three states carry information that
cannot be recovered any other way. A version that was never activated and then
dropped is a **discarded idea**. A version that ran for two weeks and was then
replaced is **superseded work**, and there is code in the repository that came
from it. Both are inactive, and anybody reading the history later needs to know
which is which.

---

## Child reference

One entry in a version's ordered list.

| Field | What it holds | Notes |
|---|---|---|
| `task_id` | The child task | A real reference |
| `position` | Where it sits in the list | Reading order, never a constraint |
| `note` | Optional line about why this step is here | Useful when the same task appears in two versions for different reasons |

**Order is advice.** It is the author's suggested sequence, and it is what a
person or an agent reads to decide where to start. It never blocks anything.
Two children that need nothing from each other can be worked on at the same
time, and readiness comes from dependencies and link states instead, which is
developed in [06](06-dependencies-and-readiness.md).

---

## Node link

A pointer from a version into the code graph, carrying a mode.

| Field | What it holds | Notes |
|---|---|---|
| `node_id` | The graph node id, if it is known | Empty for a node that does not exist yet |
| `qname` | The full name, such as `app.services.createComment` | Always present, even when `node_id` is empty |
| `kind` | `folder`, `file`, `class`, `function`, or `call` | The five real kinds, nothing else |
| `mode` | `read`, `create`, `modify`, or `delete` | `about` is reserved for anchors |
| `note` | Optional sentence about what happens here | This is where a field or a column gets described |
| `added_by`, `added_at` | Who added it and when | |

### Derived state of a link

| State | Meaning |
|---|---|
| `live` | The node exists in the graph right now |
| `pending` | A `create` link whose node does not exist yet. Expected and healthy |
| `fulfilled` | A `create` link whose node now exists. The claim came true |
| `missing` | A `read`, `modify`, or `delete` link whose node does not exist. A warning |
| `unresolved` | The node id existed once and has disappeared, usually after a rename |

### The note field is where fields and columns live

This is the practical consequence of the five node kinds rule, and it is worth
showing rather than only stating.

```
   TASK  VN-20   "Add author_id and post_id fields to Comment"

     link   mode: modify    kind: class    qname: app.models.Comment
     note   "adds author_id pointing at User and post_id pointing at Post,
             both required, both indexed"
```

The link says **where**, and the note says **what**. There is no
`Comment.author_id` node, because the parser does not produce one, and inventing
one inside the planning layer would create references that can never resolve.

---

## Anchor

A pointer from a task into the graph, with the implicit mode `about`.

| Field | What it holds |
|---|---|
| `node_id` | The graph node id |
| `qname` | The name at the time the anchor was added |
| `kind` | One of the five node kinds |

Anchors are unchanged from the current system. They sit on the task rather than
on a version, because where work lives does not change when the approach
changes. They are stored as a soft id plus a name snapshot, so a deleted node
produces a readable warning instead of a broken reference.

---

## Note

| Field | What it holds |
|---|---|
| `text` | The sentence |
| `at` | When it happened |
| `origin` | `system` or `user` |
| `author` | A person, or an agent run |

Unchanged from today, with one addition. Notes are also written when a version
is created, activated, or retired, so the story of how the approach changed
reads in the same list as everything else.

---

## Conflict decision

A collision between two pieces of work is **computed** and never stored. What
gets stored is only what a human decided to do about it.

| Field | What it holds |
|---|---|
| `node_id`, `node_qname` | Which node the argument was about |
| `task_ids` | The tasks involved, usually two |
| `modes` | What each of them intended to do to that node |
| `decision` | `ordered`, `accepted`, `resolved`, or `delegated` |
| `reason` | Why, in a sentence |
| `applied_dependency` | For `ordered`, the dependency edge that was created |
| `decided_by`, `decided_at` | Who and when |

### The four ways a collision ends

A collision means two pieces of work want to be in the same place. There are
only four honest things to do about that, and the first one is the most common.

**`ordered` — decide who goes first.** The two pieces of work are both correct
and both necessary, they simply must not happen at the same time. Choosing an
order turns a collision in space into a sequence in time, and it does so using
the one ordering edge the system already has.

```
   BEFORE                                  AFTER
   ──────                                  ─────
   function createComment()                function createComment()
        ▲              ▲                        ▲              ▲
        │ modify       │ modify                 │ modify       │ modify
   VN-11 Moderation  VN-30 Rate limiting   VN-11 Moderation  VN-30 Rate limiting
                                                 │                   ▲
   shown as: CONFLICT                            └───depends_on──────┘

                                           shown as: SEQUENCED
                                           VN-11 waits. VN-30 goes first.
```

This is the option that makes conflict handling useful rather than merely
informative. It writes a real `depends_on` edge, so the blocked side now shows
as blocked everywhere in the product, the board reflects it, and nobody has to
remember the agreement. The conflict decision keeps a record of *why* that
dependency exists, which a bare edge could never explain.

**`accepted` — we know, and it is fine.** The two pieces of work touch the same
node in ways that will not actually interfere, for example two functions being
added to the same file. The warning is dismissed with a reason, and it stays
dismissed unless the links change.

**`resolved` — change the work so they no longer collide.** Somebody narrows a
scope, moves a change into the other task, or splits a function. The links stop
overlapping and the collision disappears on its own. The decision records what
was done so the next person understands why the shape is what it is.

**`delegated` — ask somebody else to sort it out.** The people involved cannot
settle it themselves. This is the seam a future agent workflow would use, and
for now it is a record with a name attached to it.

**Tradeoff.** Storing the decision but not the collision means a decision can
quietly become irrelevant, for instance when one side drops its link entirely.
Such decisions are shown as no longer applying rather than deleted, so the
record of the conversation survives even after the reason for it is gone.

---

## Board

Unchanged from today: a set of columns, each with an id, a title, a colour, and
the two flags for whether the column counts as done and whether it is the
backlog.

One thing is added, and it belongs to the interface rather than to the stored
model: the board has a **current level**, which is the task whose children are
being shown. The root level shows every task that no active version refers to.
This is a view setting, remembered per tab.

---

## How the pieces fit together

```
   TASK  VN-3  "Add comments"
   ├─ key, title, description, type, status, priority, labels, rank
   ├─ anchors ─────────────► folder  app/comments
   ├─ depends_on ──────────► TASK VN-1  "Authentication"
   ├─ notes[]
   ├─ active_version_id ───┐
   └─ versions[]           │
        ├─ VERSION 1 ◄─────┘  "Separate Comment class"      state: active
        │    ├─ summary, document
        │    ├─ node_links[]
        │    │     read    class    Post
        │    │     create  class    Comment              ← pending
        │    │     create  function createComment()      ← pending
        │    └─ children[]
        │          1 ─► TASK VN-8   Comment model
        │          2 ─► TASK VN-9   Comment write path
        │          3 ─► TASK VN-12  Show comments on the post page
        │
        └─ VERSION 2  "Store comments inside Post"          state: draft
             ├─ summary, document
             ├─ node_links[]
             │     modify  class    Post
             └─ children[]
                   1 ─► TASK VN-15  Add a comments list to Post
                   2 ─► TASK VN-12  Show comments on the post page
                              ▲
                              └── the same task as version 1, position 3
```

---

## Everything that is derived, in one list

This is the list to check whenever somebody proposes a new field. If the
proposed field appears here, it should not be stored.

| Derived value | Computed from |
|---|---|
| parents of a task | the containment index over active versions |
| all parents, including inactive ones | the containment index over every version |
| shared, orphaned | how many active versions refer to the task |
| depth and breadcrumb path | walking up the containment index |
| blocked | the status of everything in `depends_on` |
| blocks | the reverse of other tasks' `depends_on` |
| waiting on code | link states on the active version |
| ready | not blocked and not waiting |
| progress | children of the active version, deduplicated |
| rollup blocking | whether any descendant is blocked |
| effective links | a task's links merged with its descendants' links |
| link state, including pending and fulfilled | whether the node exists in the graph now |
| verified | every `create` link fulfilled |
| contested nodes | write mode links from two or more open tasks on one node |
| sequenced instead of contested | a conflict decision of `ordered`, plus its dependency |
| node to task lookup | the link index |

The next file, [04 — Lifecycle and status](04-lifecycle-and-status.md), covers
how a task and a version move between states, and what "done" means when work
is a tree rather than a flat list.
