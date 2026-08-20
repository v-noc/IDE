# 01 — Concepts

This file defines every term the design uses. Each concept gets a definition, a
statement of what it is deliberately **not**, an example, and where it makes a
difference, the tradeoff involved in defining it that way.

The list is short on purpose. There is one kind of thing you store (Task), three
stored edges between things, and that is all. Everything else in the product is
computed from those.

```
   THINGS YOU STORE                STORED EDGES
   ────────────────                ──────────────
   Task                            child ──parent_id──► task
   Conflict decision               task  ──depends_on──► task
                                   task  ──node_link──► graph node (with mode)
```

---

## Task

**A task is a promise that something will become true, together with the
material somebody needs in order to make it true.**

A task is the only kind of work object in the system. It is what the board
shows, what a person is assigned, what carries a status, what other work waits
for, and what contains smaller work. Whether it represents three weeks of
design or twenty minutes of typing, it is the same kind of object with the same
capabilities.

Every task carries two pieces of writing with different jobs. The
**description** is one short paragraph for somebody scanning a board, and the
**document** is the long write-up for somebody who has decided to do the work.
Keeping them separate matters, because a description long enough to be useful
is too long to scan, and a description short enough to scan is too thin to work
from.

```
   TASK  VN-9   Comment write path                    ● in progress
   ─────────────────────────────────────────────────────────────────
   description  Saving a comment needs one function that validates the
                post, attaches the author, and stores the row.

   document     ## Approach
                The service layer owns validation, the repository owns
                storage. createComment() takes the post id, the body text,
                and the current user, then …
                ## Things considered and rejected
                Putting validation in the repository was rejected because …
```

**A task is not:**

- *A line in a checklist.* A checklist line has a title and a checkbox. A task
  has reasoning, code links, children, and a history.
- *A fixed size.* Nothing about a task says whether it is big or small. Size
  shows up as depth in the tree, and depth can change at any time.
- *A different type when it is small.* There is no separate object for a small
  piece of work. A leaf task is a task.
- *Owned by whoever created it.* A task carries its own status and history
  independent of who is working on it.

**Tradeoff.** Making every piece of work a full task means every piece of work
carries fields it may not need, and a five-minute step ends up with a document
field it will never use. That is accepted because the alternative, which is a
lightweight type that gets upgraded to a real task later, means conversions,
two sets of rules, and arguments about which type to use.

---

## Parent and position

**A task has exactly one parent, stored as `parent_id`. The parent field is null
for top-level tasks. Siblings are ordered by `position` (lexorank).**

This creates a tree: every task knows who its parent is, and children of a task
are found by querying "which tasks have `parent_id = this task's id?", ordered
by their `position` values.

```
   TASK  VN-3  "Add comments"
     parent_id = null            (top-level)
     position = "1"
     
     TASK  VN-8  "Comment model"
       parent_id = VN-3          (child of VN-3)
       position = "1.1"
       
     TASK  VN-9  "Comment write path"
       parent_id = VN-3          (child of VN-3)
       position = "1.2"
```

The order is real information. It is the author's advice about a sensible
sequence, and it is what an agent or a person reads to decide where to start.
The order is **not** a constraint, and it never blocks anything. Two children
that need nothing from each other can be worked on at the same time, and
readiness is worked out from real dependencies rather than from position.

**Parent is not:**

- *Shared.* A task has exactly one parent. If two pieces of work need to share a
  step, one depends on the other.
- *Implicit from order.* The parent field stores the edge explicitly. Position
  is advice about sequence, not a dependency.

**Tradeoff.** Single parent makes the tree structure simple and unambiguous. If
work is genuinely shared between two approaches, it should be stored under one
parent and the other side should depend on it. This is more honest about what
the relationship actually means.

---

## Anchor

**An anchor says roughly where in the codebase a task lives, and it survives
every change of approach.**

An anchor is a soft pointer to a graph node with the mode `about`. It is
deliberately vague. It answers "if I am looking at this part of the code, which
work is around here?" rather than "what exactly will change?".

```
   TASK VN-9  "Comment write path"
     anchor  ──about──►  file  comment_service.py
```

Anchors already exist in the current system and their behaviour does not
change. They are stored as a soft node id plus a snapshot of the node's name
and kind, so that when the parser deletes the node, the anchor shows a warning
with its last known name rather than turning into a broken reference.

**An anchor is not:**

- *A statement that the task will change that code.* That is what affected
  nodes are for.
- *Part of a version.* There are no versions. Anchors sit on the task.
- *A hard database link.* The parser rewrites the graph constantly. A hard link
  would either block the parser or break.

---

## Node link, and the five modes

**A node link is a pointer from a task to a graph node, carrying a mode that
says what the work does to that node.**

This is one mechanism that produces two lists on screen.

| Mode | Meaning | Shown as | Counts as a write? |
|---|---|---|---|
| `about` | This work is around here somewhere. Used by anchors. | anchor chip | no |
| `read` | Somebody must read this to do the work, but it will not change. | **Context** | no |
| `create` | This node does not exist yet and this work will create it. | **Affects** | yes |
| `modify` | This node exists and this work will change it. | **Affects** | yes |
| `delete` | This node exists and this work will remove it. | **Affects** | yes |

```
   TASK VN-9 "Comment write path"
     CONTEXT                         AFFECTS
     ───────                         ───────
     read  ──► class Post            create ──► function createComment()
     read  ──► class User            modify ──► class Comment
     read  ──► function current_user()
```

Two properties of node links carry a lot of the design's value.

**A link can point at code that does not exist yet.** A `create` link names a
node by its intended name and kind before anything has been written. Until the
node appears in the graph the link is *pending*, and when a node with that name
appears the link becomes *fulfilled*. This is what allows the system to check a
claim rather than believe it.

**Links roll up the tree.** A parent's effective link set is its own links
combined with every descendant's links. Nobody types links on "Add comments";
the system knows what it touches because its children said so.

**A node link is not:**

- *A pointer at a field, a column, a parameter, or an endpoint.* Those are not
  nodes. The link points at the class or function that contains them, and the
  task's own words describe the detail.
- *A hard database link.* Same reasoning as anchors.
- *A permission.* It describes intent. Whether it is later used to scope what
  an agent is allowed to change is a separate decision, discussed in
  [12 — Agent seams](12-agent-seams.md).

**Tradeoff.** Asking people to record modes is extra work, and people will
sometimes get them wrong, marking something `read` and then changing it. The
system can catch that afterwards by comparing the links against what actually
changed in the commits, so a wrong mode becomes a correctable observation
rather than a silent lie. The benefit, which is automatic collision detection
and automatic readiness, is only possible if the modes exist.

---

## Dependency

**A dependency says that one task cannot be finished until another task is
finished.**

It is stored as a link from task to task, and it is the only ordering
relationship in the system that a person writes down by hand.

```
   VN-9  "Comment write path"  ──depends_on──►  VN-5  "Write current_user()"
```

Dependencies can connect tasks at any depth and in any part of the tree, which
is what allows them to be as precise as the real reason. One rule constrains
them: **a task may never depend on its own ancestor or its own descendant**,
because containment already describes that relationship and combining the two
produces a deadlock.

**A dependency is not:**

- *The same as containment.* A child is part of its parent. A dependency
  connects two pieces of work where neither is part of the other.
- *Automatically created by position.* Being later in a list is not a
  dependency.
- *The only source of blocking.* A task can also be waiting because the code it
  needs does not exist yet. That is derived from node links rather than stored.

---

## Blocked, ready, and other derived states

**Derived states are computed on every read and never stored.**

The list of them is short and each one is defined precisely in later files.

| Name | Meaning |
|---|---|
| blocked | A task this one depends on is not finished |
| waiting on code | A `read` or `modify` link points at a node that does not exist yet |
| ready | Not blocked and not waiting |
| progress | How many children are finished |
| verified | Every `create` link now points at a node that really exists |
| depth | Distance from the root |
| breadcrumb | Path from the root to this task |
| contested | Two pieces of open work have write modes on the same node |

The reason none of these are stored is that all of them can change without
anybody touching the task. A reparse deletes a node, somebody else finishes
their work, a parent or child is moved. A stored flag would be wrong within
minutes and nobody would know which stored flags were stale.

**Tradeoff.** Deriving means computing, and computing costs time on every read.
The design accepts that and pays for it with batching and caching, described in
[09 — Architecture](09-architecture.md). Correctness that costs milliseconds
beats speed that lies.

---

## Conflict decision

**A conflict decision records what a human decided about a collision. The
collision itself is never stored.**

When two pieces of open work both intend to change the same node, the system
computes that fact fresh every time. What it cannot compute is whether the
people involved have talked about it. So the only thing stored is the decision.

```
   COMPUTED   function createComment() ← modify by VN-11 and by VN-30
   STORED     "VN-11 and VN-30 on createComment(): ordered by Yared,
               reason: VN-11 waits for VN-30"
```

**A conflict decision is not:**

- *A record that a conflict exists.* If the links change so the collision
  disappears, the decision simply stops applying and is shown as resolved.
- *A lock.* It does not prevent anybody from doing anything.

---

## Board, level, and status

**The board shows the children of one task at a time, arranged in columns by
status.**

The current board and its columns are kept exactly as they are. What is added
is the idea of a **level**. The board has a current task whose children it is
showing, starting at the root, and a breadcrumb for moving up and down.

```
   ▸ root                      showing every task with parent_id = null
   ▸ root ▸ Comments           showing the children of VN-3
   ▸ root ▸ Comments ▸ Model   showing the children of VN-8
```

**Status** stays exactly what it is today, which is the id of a board column.
It lives on the task, because moving a card between columns is a statement about
the work.

**The board is not:**

- *A view of the whole tree.* It never shows two levels of children at once.
  Seeing structure across levels is the job of the tree view in the sidebar and
  of the task detail panel.
- *The only entry point.* A task can also be reached from a code node, from
  search, or from the canvas.

---

## Event

**An event is a typed history entry, recording something that happened to the
task.**

Events replace prose notes. They are machine-readable and can be rendered into
English at display time. System events are written automatically (status
changed, link added, dependency added), and user events are typed by people
(comments, notes).

```
   { type: "status_changed", payload: {from: "todo", to: "doing"}, … }
   { type: "link_added", payload: {mode: "create", qname: "app.services.createComment"}, … }
   { type: "comment", payload: {text: "This is going to be tricky"}, … }
```

**An event is not:**

- *A permanent record that something was true.* Events record decisions and
  changes, not conclusions. `blocked` is derived from `depends_on`, not from a
  `blocked` event.
- *A journal.* The event list tells a story of changes and decisions, not a
  second-by-second log.

---

## Summary table

| Concept | Stored? | Lives on | Can it disappear without warning? |
|---|---|---|---|
| Task | yes | itself | only if a person deletes it |
| Parent (parent_id) | yes | the child task | only if a person deletes or reparents it |
| Position | yes | the task | when the child list order changes |
| Anchor | yes | a task | its target node can, leaving a warning |
| Node link | yes | a task | its target node can, leaving a warning |
| Dependency | yes | a task | only if a person deletes it |
| Event | yes | a task | only if a person deletes the whole task |
| Conflict decision | yes | its own record | no |
| Blocked, ready, progress, contested, depth, breadcrumb, and the rest | **no** | computed | they change constantly, which is why they are not stored |

The next file, [02 — Relationships](02-relationships.md), works through the
candidate relationship types one at a time and explains why only three of them
survive as stored edges.
