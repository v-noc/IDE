# 02 — Relationships

A relationship type is not free. Every one that exists is a question the user
has to answer correctly for as long as the product does, and if two of them can
be confused with each other, the database quietly fills with data that means
nothing. Queries built on that data then produce confident wrong answers, which
is worse than having no data at all.

So the model stores three relationships and computes everything else. Each of
the three earns its place by passing the same test:

> **Does this record something that cannot be worked out from what is already
> stored, and does it change a decision somebody makes?**

If it can be computed, it is computed. If it does not change anybody's
behaviour, it does not exist.

```
   STORED  (there are three)
   ─────────────────────────────────────────────────────────────
   child ──parent_id──────────►  task         how work nests
   task  ──depends_on─────────►  task         what must come first
   task  ──node_link + mode───►  graph node   which code it touches
                                   read · create · affects · delete
```

Three arrows. The rest of this file defines each one, and the last two sections
show what is derived from them and what has to be true before a fourth is ever
added.

---

## 1 — parent, stored on the child as `parent_id`

**What it is.** One task is a child of another task, forming a tree.

**Why it is stored.** The structure of the work is not derivable from anything
else. Somebody decided that "Comment model" is part of "Add comments", and that
decision *is* the structure of the work.

**Why it lives on the child.** A task has exactly one parent. Storing the edge
on the child enforces this at the field level: either the field is null, and the
task is top-level, or it points at exactly one parent. There is no sharing, no
task appearing in two places, and no degenerate cases to handle.

```
   TASK  VN-3  "Add comments"
     parent_id = null    (top-level)

     TASK  VN-8  "Comment model"
       parent_id = VN-3

     TASK  VN-9  "Comment write path"
       parent_id = VN-3
```

When two pieces of work genuinely need to share a step, one of them depends on
the other. Dependencies are the tool for shared work; containment is not.

**Ordering.** Children are ordered by a `position` field (lexorank, like `rank`
for board columns), so the tree is completely deterministic. There is no second,
competing list of children anywhere — the child list is read from the
`parent_id` index and sorted by `position`.

**Tradeoff.** Finding a task's parent is a read of one field. Finding its place
in the tree means walking `parent_id` upward. Both are O(depth), and depth is
bounded by what a person can navigate, which is far smaller than the number of
tasks.

---

## 2 — depends_on, between two tasks

**What it is.** One task cannot be finished until another task is finished.

**Why it is stored.** Some ordering has no trace in the code at all. "Do not
start the filtering work until moderation ships, because we only want to
maintain one of them at a time" is a decision, not a fact about functions.
Nothing can derive it.

**Why it connects tasks and only tasks.** Every piece of work in this system is
a task, so the edge can be as precise as the real reason. If the truth is "I
need that one function", the edge points at the small task that writes that
function, not at the large task that happens to contain it.

```
   VN-9   Comment write path  ──depends_on──►  VN-5   Write current_user()
     child of VN-3 Comments                      child of VN-1 Authentication
```

**The guard.** A task may never depend on its own ancestor. Containment already
says "this is part of that", and adding a dependency on top of it produces a
deadlock that no order of work can resolve.

```
   REFUSED                              WHY
   ───────                              ───
   VN-3  contains   VN-11               VN-3 is not finished until VN-11 is
   VN-11 depends_on VN-3                VN-11 cannot start until VN-3 is

                                        Neither can ever finish. Refused.
```

A task depending on its own descendant is not a deadlock, only redundant —
containment already says the same thing — so the system drops it silently and
writes an event.

**Direction.** The edge is stored once, pointing from the task that waits to the
task it waits for. The opposite reading, "VN-5 blocks VN-9", is the same fact
seen from the other end and is computed when asked. So is the state *blocked*,
which is simply "something this depends on is not done yet".

**Tradeoff.** Allowing dependencies at any depth means the graph can become
large and cross-cutting, and somebody looking at a high-level card will not
immediately see that something four levels down is stuck. The design pays for
this by rolling blocking status up the tree, so a parent card shows that
something inside it is blocked, with a link to the exact task.

---

## 3 — node_link with a mode, from a task into the code graph

**What it is.** A task points at a node in the code graph, and every pointer
carries a mode saying what the work does to that node: `read`, `create`,
`affects`, or `delete`.

**Why it is one mechanism with a mode, and not several link types.** The most
valuable question in the system is asked from the code side, not the work side —
standing on `function createComment()` and asking who is about to touch it. One
list with a mode column answers that in a single pass.

```
   Standing on  function createComment()  and asking
   "who is about to touch this?"

   VN-11  affects   ← a collision
   VN-30  affects   ← a collision
   VN-40  read      ← worth knowing, not a collision
```

Splitting reading and writing into separate relationship types would make that
one question into two queries that have to be kept in step in every screen
forever, and would raise a question nobody can answer correctly — *which list
does this belong in?* — every time a link is created.

**Why the modes are exactly these four.**

- `read` means look but do not change.
- `create`, `affects`, and `delete` are the three things work can do to a node,
  and they are distinguished because they behave differently:
  - Two `create` links on the same name are a duplicate.
  - A `delete` underneath somebody else's `affects` is severe.
  - A `create` is the one mode allowed to point at a node that does not exist
    yet.

On screen the read-mode links are shown as **Context** and the write-mode links
as **Affects**, because those are the words people use. That is presentation.
Underneath there is one list.

**Soft references.** A link is stored as a node id plus a snapshot of the node's
name and kind. The parser deletes and recreates nodes whenever a file changes,
so a link that hardened onto an id alone would break constantly. With the
snapshot, a vanished node produces a readable warning instead of a dangling
pointer.

**Tradeoff.** Four modes is more than one, and people will sometimes pick the
wrong one. The design accepts this because a wrong mode is detectable: after the
work lands, the commits say which nodes actually changed, and the system can
point out that a task marked something `read` and then rewrote it. A mistake
that can be noticed is much better than a distinction that was never recorded.

---

## What is derived, on every read

None of the following is stored. All of it is computed from the three arrows at
the moment somebody asks, which is why none of it can ever be stale or disagree
with the data underneath.

```
   children of a task               from the parent_id index, in reverse
   parent of a task                 from parent_id (at most one)
   blocks — the reverse view        from depends_on
   blocked / ready                  from depends_on plus link states
   progress                         from the task's children
   where the work lives             from the nearest container of its links
   effective links of a parent      from the union of its descendants' links
   contested nodes                  from write-mode links on the same node
   depth / breadcrumb path          from walking parent_id up to the root
```

---

## The two laws underneath

### Law 1 — Point hard references at durable things only

Anything a person can throw away must not be the target of a stored reference.

```
   DURABLE                       FRAGILE
   ───────                       ───────
   a task                        a graph node id on its own
   a graph node id + name        a graph node's position in a file
```

Tasks are durable, so dependencies point at tasks and parents are tasks. Graph
nodes are fragile, because the parser deletes and recreates them whenever a file
changes, so every pointer into the graph carries the name and kind snapshot from
above.

### Law 2 — One fact, one place

If a fact is stored twice, the two copies will disagree, and no amount of
careful code prevents it forever. So `depends_on` is stored in one direction
only, `parent_id` is stored only on the child, a collision between two tasks is
not stored at all — only the human decision about it — and progress, blocking,
readiness and contested nodes are never stored.

---

## Before a fourth arrow is added

This list will be reopened, by a person copying another tracker's schema or by
an agent asked to "add support for related tasks". Four checks stop the common
mistakes, and they are cheap to run.

```
   ASK                                       IF YES, IT IS NOT A RELATIONSHIP
   ───                                       ────────────────────────────────
   Is it an existing edge read backwards?    compute it, do not store it
   Does an existing edge already mean this?  reuse the word already in use
   Can two people disagree about what to     it will fill with noise
     do when it is set?
   Is it something you do once, rather       it is a command, not a column
     than something that stays true?
```

Only if all four are no does the test at the top of this file apply: it must
record something not derivable, **and** change a decision. Both, not either.

---

The next file, [03 — Data model](03-data-model.md), turns these three arrows
into concrete fields and marks clearly which are written and which are
calculated.
