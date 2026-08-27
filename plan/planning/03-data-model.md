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
     ├── Node link      pointer to a graph node, with a mode
     ├── Event          typed history entry
     └── Dependency     pointer to another task

   Conflict decision    what a human decided about a collision
   Board                columns, unchanged from today
```

---

## Task

The task is the unit of work, the unit of display, and the unit of dependency.
A task has exactly one parent (stored as `parent_id`). No shared children, no
DAG.

### Stored fields

| Field | What it holds | Notes |
|---|---|---|
| `id` | The internal identifier | Never shown to people |
| `key` | The human key, such as `VN-9` | Flat, never reused |
| `title` | One line | What the card shows |
| `description` | One short paragraph | For scanning. Plain text or light markdown |
| `type` | `epic`, `task`, `bug`, or `improvement` | A label for filtering, not structure |
| `status` | The id of a board column | Unchanged from today |
| `priority` | `none`, `low`, `medium`, `high`, `urgent` | Unchanged from today |
| `labels` | A set of free text chips | Unchanged from today |
| `rank` | Position within its column | Ordering for drag and drop |
| `parent_id` | Another task, or null | null means top-level. Single parent enforced. |
| `position` | Order among siblings | Lexorank, same scheme as `rank` |
| `document` | The long write-up, in markdown | The main body of thinking |
| `node_links` | List of links into the graph | Each with a mode: read, create, affects, delete. The only way a task points at code. |
| `depends_on` | Set of task references | Dependencies, one stored edge |
| `verified_by_tests` | Test node references, optional | Second verification source; see [05](05-graph-links.md) §6 |
| `events` | List of typed events | Typed history, replaces prose notes |
| `deleted_at` | Timestamp, or null | Soft delete for undo |
| `deleted_batch_id` | Shared by all tasks deleted together | For atomic restore |
| `created_by` | A person, or an agent run | |
| `created_at`, `updated_at` | Timestamps | |

### Derived values

| Value | How it is worked out |
|---|---|
| `children` | Every task whose `parent_id` is this task's id, ordered by `position` |
| `parents` | This task's `parent_id`, yielding at most one parent (not derived, but single) |
| `breadcrumb` | Walking up via `parent_id` to the root |
| `depth` | Distance from the nearest root |
| `blocked` | Something in `depends_on` is not finished |
| `blocks` | The reverse view of other tasks' `depends_on` |
| `waiting_on_code` | A `read`, `affects`, or `delete` link points at a node that does not exist |
| `ready` | Not blocked and not waiting on code |
| `progress` | Finished children over total |
| `verified` | A `verified` event exists for this task (see [05](05-graph-links.md) §6) |
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
| `children` | Derived from `parent_id` on children, not stored |
| `all_parents` | Not applicable; each task has exactly one parent |
| `is_shared` | Not applicable; no shared children |
| `is_orphaned` | Not applicable; cascade delete removes this concept entirely |
| `is_blocked` | Changes when other people finish their work. Derived |
| `progress_count` | Changes when any child changes. Derived |
| `versions` | Removed. Document and node_links live on the task directly. |
| `estimate` | Postponed on purpose. Estimation is a feature with its own opinions. |
| `assignee` | Also postponed |

---

## Node link

A pointer from a task into the code graph, carrying a mode. Lives on the task.

| Field | What it holds | Notes |
|---|---|---|
| `node_id` | The graph node id, if known | Empty for a node that does not exist yet |
| `qname` | The full name, such as `app.services.createComment` | Always present, even when `node_id` is empty |
| `kind` | `folder`, `file`, `class`, `function`, or `call` | The five real kinds, nothing else |
| `mode` | `read`, `create`, `affects`, or `delete` | Four modes. There is no vague mode. |
| `note` | Optional sentence about what happens here | This is where a field or a column gets described |
| `container` | Node id + name snapshot of the file/class | For unresolved `create` links |
| `added_by`, `added_at` | Who added it and when | |

### Derived state of a link

| State | Meaning |
|---|---|
| `live` | The node exists in the graph right now |
| `pending` | A `create` link whose node does not exist yet. Expected and healthy |
| `fulfilled` | A `create` link whose node now exists. The claim came true |
| `missing` | A `read`, `affects`, or `delete` link whose node does not exist. A warning |
| `unresolved` | The node id existed once and has disappeared, usually after a rename |

### The note field is where fields and columns live

This is the practical consequence of the five node kinds rule.

```
   TASK  VN-20   "Add author_id and post_id fields to Comment"

     link   mode: affects    kind: class    qname: app.models.Comment
     note   "adds author_id pointing at User and post_id pointing at Post,
             both required, both indexed"
```

The link says **where**, and the note says **what**. There is no
`Comment.author_id` node, because the parser does not produce one.

### `affects` is about the node itself

A link's mode describes what happens to **that node**, never to what it
contains. Adding a method to a class is one link on the new function, and the
class's involvement is derived from containment:

```
   TYPED     create   function  Comment.validate    container: class Comment
   DERIVED   touches  class Comment · file models.py
```

`affects class Comment` is written only when the class itself changes. Without
this rule two tasks adding different methods to one class would both claim to
affect the class and be reported as colliding.

Derived containment carries no state. Only explicit links are `pending`,
`fulfilled`, `missing`, or `unresolved`.

### Where the work lives is derived

No link is primary, and no field records a location. The location shown in a
breadcrumb or on the canvas is the nearest container holding every linked node,
used only when it is specific enough to be useful. Otherwise the linked nodes
are listed instead. This is a display rule; nothing is stored for it.

---

## Event

Typed history entry, replacing prose notes. Machine-readable and renderable at
display time.

| Field | What it holds | Notes |
|---|---|---|
| `type` | The event kind | `status_changed`, `link_added`, `dependency_added`, `task_created`, `parent_changed`, `deleted`, `restored`, `verified`, `conflict_decided`, `comment` |
| `payload` | Type-specific data | Structured, not prose |
| `at` | When it happened | |
| `origin` | `system`, `user`, or `agent` | |
| `author` | A person, or an agent run | |

Examples:

```
{ type: "status_changed", payload: {from: "todo", to: "doing"}, at: "2026-08-20T14:30:00Z", origin: "user", author: "alice" }

{ type: "link_added", payload: {mode: "create", kind: "function", qname: "app.services.createComment"}, at: "2026-08-20T14:31:00Z", origin: "user", author: "alice" }

{ type: "verified", payload: {link_qnames: ["app.services.createComment"], node_ids: ["node_12345"], graph_revision: "abc123"}, at: "2026-08-20T14:32:00Z", origin: "system", author: "alice" }

{ type: "comment", payload: {text: "This is going to be tricky"}, at: "2026-08-20T14:33:00Z", origin: "user", author: "alice" }
```

Render the English sentence from `type` + `payload` at display time. Do not
store the sentence. A free-text human comment is just `type: "comment"` with
`payload: {text}`.

---

## Dependency

One entry in a task's `depends_on` list.

| Field | What it holds | Notes |
|---|---|---|
| `task_id` | The blocking task | A real reference to another task |

That is it. Dependencies are simple references. The ordering of the list does
not matter; readiness comes from whether the blocking tasks are finished, which
is developed in [06](06-dependencies-and-readiness.md).

---

## Conflict decision

A collision between two pieces of work is **computed** and never stored. What
gets stored is only what a human decided to do about it.

| Field | What it holds |
|---|---|
| `node_id`, `node_qname` | Which node the argument was about |
| `task_ids` | The tasks involved, usually two |
| `modes` | What each of them intended to do to that node |
| `decision` | `ordered` or `accepted` |
| `reason` | Why, in a sentence |
| `applied_dependency` | For `ordered`, the dependency edge that was created |
| `decided_by`, `decided_at` | Who and when |

The two ways a collision ends: **`ordered`** (one goes first, creating a real
dependency), or **`accepted`** (the warning is dismissed with a reason).

---

## Board

Unchanged from today: a set of columns, each with an id, a title, a colour, and
the two flags for whether the column counts as done and whether it is the
backlog.

One thing is added, and it belongs to the interface rather than to the stored
model: the board has a **current level**, which is the task whose children are
being shown. The root level shows every task whose `parent_id` is null.
This is a view setting, remembered per tab.

---

## The three stored edges

```
child ──parent_id──► task
task  ──depends_on──► task
task  ──node_link (with mode)──► graph node
```

A task points at code in exactly one way.

---

## How the pieces fit together

```
   TASK  VN-3  "Add comments"
   ├─ key, title, description, type, status, priority, labels, rank
   ├─ parent_id = null    (top-level)
   ├─ position = 0.1      (first among siblings)
   ├─ depends_on ─────────► TASK VN-1  "Authentication"
   ├─ document = "..."
   ├─ node_links[]
   │    read    class    Post
   │    create  class    Comment              ← pending
   │    create  function createComment()      ← pending
   └─ events[]
        { type: "task_created", ... }
        { type: "link_added", payload: {mode: "read", ...}, ... }
        { type: "link_added", payload: {mode: "create", ...}, ... }

   TASK  VN-8  "Comment model"
   ├─ key, title, ...
   ├─ parent_id = VN-3    (child of VN-3)
   ├─ position = 0.1      (first child)
   └─ ...

   TASK  VN-9  "Comment write path"
   ├─ key, title, ...
   ├─ parent_id = VN-3    (child of VN-3)
   ├─ position = 0.2      (second child)
   └─ ...
```

---

## Everything that is derived, in one list

This is the list to check whenever somebody proposes a new field. If the
proposed field appears here, it should not be stored.

| Derived value | Computed from |
|---|---|
| children of a task | `parent_id` index in reverse, ordered by `position` |
| breadcrumb path | Walking up via `parent_id` to the root |
| depth | Distance from the root |
| blocked | The status of tasks in `depends_on` |
| blocks | The reverse of other tasks' `depends_on` |
| waiting on code | Link states on the task's node_links |
| ready | Not blocked and not waiting |
| progress | Finished children over total |
| effective links | A task's links merged with its descendants' links |
| link state (pending, fulfilled, missing, unresolved) | Whether the node exists in the graph now |
| verified | Every `create` link fulfilled at a recorded graph revision |
| contested nodes | Write mode links from two or more open tasks on one node |
| sequenced instead of contested | A conflict decision of `ordered`, plus its dependency |
| node to task lookup | The link index (both `node_id` and `qname` directions) |

The next file, [04 — Lifecycle and status](04-lifecycle-and-status.md), covers
how a task moves between states and what "done" means when work is a tree rather
than a flat list.
