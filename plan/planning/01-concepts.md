# 01 — Concepts

This file defines every term the design uses. Each concept gets a definition, a
statement of what it is deliberately **not**, an example, and where it makes a
difference, the tradeoff involved in defining it that way.

The list is short on purpose. There are three things you store, two
relationships between them, and one pointer into the code graph. Everything
else in the product is computed from those.

```
   THINGS YOU STORE                RELATIONSHIPS               POINTER
   ────────────────                ─────────────               ───────
   Task                            version → child tasks       task → graph node
   Version                         task → task (depends_on)      with a mode
   Conflict decision
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
- *Owned by whoever created it.* A task can be referred to as a child by more
  than one parent version, and it survives when any of them changes.

**Tradeoff.** Making every piece of work a full task means every piece of work
carries fields it may not need, and a five-minute step ends up with a document
field it will never use. That is accepted because the alternative, which is a
lightweight type that gets upgraded to a real task later, means conversions,
two sets of rules, and arguments about which type to use.

---

## Version

**A version is one answer to the question "how are we going to do this?"**

A version holds the approach: the long document, the code the approach reads,
the code the approach changes, and the ordered list of child tasks the approach
needs. A task always has at least one version, and exactly one version is
active at any moment.

```
   TASK  "Add comments"
     ├── version 1  "Separate Comment class"     ★ ACTIVE
     └── version 2  "Store comments in Post"     draft
```

While a task has only one version, the interface never says the word "version".
The document, the context list, the affects list, and the children look like
plain fields on the task. The concept only becomes visible when somebody
deliberately creates an alternative.

**A version is not:**

- *An owner of its children.* This is the most important sentence in the file.
  A version holds an ordered list of references to child tasks. The children
  exist independently, and deleting or retiring a version never deletes them.
- *A snapshot of the past.* Versions are not a history feature. Task history
  lives in commits and in notes. A version is a live alternative that somebody
  might activate.
- *A copy of the task.* It does not duplicate the title, status, priority, or
  dependencies. Those live on the task and are shared.
- *Required to be more than one.* Most tasks have exactly one version forever,
  and that is the normal case rather than a degenerate one.

**Tradeoff.** Putting the document, links, and children on the version rather
than directly on the task adds one hop of indirection to every read. In return,
a person can write down two competing approaches side by side, compare them,
choose one, and keep the rejected one as a record of what was considered. The
indirection is hidden while a task has one version, which is almost always.

---

## Child reference

**A child reference is one entry in a version's ordered list, pointing at
another task.**

It is the only way one task becomes part of another. There is no separate
parent field on the child. If you want to know who a task's parents are, you
ask which versions refer to it, which the system indexes.

```
   VERSION 1 of VN-3 "Add comments"
     position 1  ──►  VN-8   Comment model
     position 2  ──►  VN-9   Comment write path
     position 3  ──►  VN-10  Comment read path
     position 4  ──►  VN-11  Comment moderation
     position 5  ──►  VN-12  Show comments on the post page
```

The order is real information. It is the author's advice about a sensible
sequence, and it is what an agent or a person reads to decide where to start.
The order is **not** a constraint, and it never blocks anything. Two children
that need nothing from each other can be worked on at the same time, and
readiness is worked out from real dependencies rather than from position.

**A child reference is not:**

- *Exclusive.* The same task can be referenced by two versions of the same
  parent, and by versions of different parents. That is how work shared between
  two approaches, or genuinely shared between two areas, is represented.
- *A dependency.* Being second in the list does not mean waiting for the first.
- *A copy.* Removing a reference removes the reference, not the task.

**Tradeoff.** Because parenthood is a reference rather than a field on the
child, a task can end up with two parents, and the tree is really a directed
graph. That is more honest, since shared work genuinely exists, but it means
the interface must show when a task has more than one parent, and progress
counting has to avoid counting the same task twice.

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
- *Part of a version.* Anchors sit on the task, because where the work lives
  does not change when the approach changes.
- *A hard database link.* The parser rewrites the graph constantly. A hard link
  would either block the parser or break.

---

## Node link, and the five modes

**A node link is a pointer from a version to a graph node, carrying a mode that
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
   VERSION 1 of VN-9 "Comment write path"

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
| progress | How many children of the active version are finished |
| verified | Every `create` link now points at a node that really exists |
| orphaned | No active version of any task refers to this one |
| shared | More than one active version refers to this one |
| contested | Two pieces of open work have write modes on the same node |

The reason none of these are stored is that all of them can change without
anybody touching the task. A reparse deletes a node, somebody else finishes
their work, a version is activated elsewhere. A stored flag would be wrong
within minutes and nobody would know which stored flags were stale.

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
   STORED     "VN-11 and VN-30 on createComment(): accepted by Yared,
               reason: VN-30 lands first and VN-11 rebases"
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
   ▸ root                      showing every task with no parent
   ▸ root ▸ Comments           showing the children of the active version of VN-3
   ▸ root ▸ Comments ▸ Model   showing the children of VN-8
```

**Status** stays exactly what it is today, which is the id of a board column.
It lives on the task, not on the version, because moving a card between columns
is a statement about the work and not about the approach.

**The board is not:**

- *A view of the whole tree.* It never shows two levels of children at once.
  Seeing structure across levels is the job of the tree view in the sidebar and
  of the task detail panel.
- *The only entry point.* A task can also be reached from a code node, from
  search, or from the canvas.

---

## Note

**A note is one entry in a task's activity list, written either by a person or
by the system.**

This already exists and does not change. System notes are short factual
sentences appended when something happens, such as a status change, an anchor
being added, or a version being activated. User notes are whatever somebody
types. Both live in the same list so the history reads in one sequence.

Notes are the reason the system can afford to derive so much. When a version is
activated or a dependency is added, the fact that it happened is recorded as a
sentence, even though the current state is computed. You keep the story without
storing the state twice.

---

## Summary table

| Concept | Stored? | Lives on | Can it disappear without warning? |
|---|---|---|---|
| Task | yes | itself | only if a person deletes it |
| Version | yes | a task | only if a person deletes it |
| Child reference | yes | a version | when the version is edited |
| Anchor | yes | a task | its target node can, leaving a warning |
| Node link | yes | a version | its target node can, leaving a warning |
| Dependency | yes | a task | only if a person deletes it |
| Conflict decision | yes | its own record | no |
| Blocked, ready, progress, contested, and the rest | **no** | computed | they change constantly, which is why they are not stored |

The next file, [02 — Relationships](02-relationships.md), works through the
candidate relationship types one at a time and explains why only two of them
survive as stored edges.
