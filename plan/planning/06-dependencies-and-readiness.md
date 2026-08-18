# 06 — Dependencies and Readiness

The question this file answers is the one people ask a planning tool most
often: **what can I actually start right now?**

Getting to a good answer needs three things. Somewhere to record ordering that
only a human knows about. A way to work out ordering that the code already
implies. And a set of rules strict enough that the dependency graph stays
readable instead of turning into a web nobody trusts.

---

## 1. One stored edge, pointing at tasks, at any depth

There is exactly one ordering relationship you can write down by hand:

```
   TASK  ──depends_on──►  TASK
```

Because every piece of work in this system is a task, the edge can be as
precise as the real reason. The real reason is rarely "all of authentication
must ship". It is usually "I need the one function that tells me who the
current user is".

```
   COARSE, AND USUALLY WRONG              PRECISE, AND USUALLY RIGHT
   ─────────────────────────              ──────────────────────────
   VN-3  Add comments                     VN-9   Comment write path
     ──depends_on──►                        ──depends_on──►
   VN-1  Authentication                   VN-5   Write current_user()

   Comments cannot start at all until     Only the write path waits, and only
   every part of auth is finished,        for one function. Everything else
   including password reset.              in comments proceeds immediately.
```

The coarse edge is not just imprecise. It is actively harmful, because it makes
four tasks wait for work none of them need, and people learn to ignore blocked
chips that are usually wrong.

Nothing stops you from writing the coarse edge when the coarse edge is the
truth. Sometimes it is. The point is that the model does not force it.

---

## 2. The two guards

### Guard 1 — no dependency between a task and its own ancestor or descendant

```
   REFUSED                                 WHY
   ───────                                 ───
   VN-3   ──contains──►    VN-11           VN-3 is not finished until VN-11 is
   VN-11  ──depends_on──►  VN-3            VN-11 cannot start until VN-3 is

                                           Neither one can ever finish.
```

Containment already says "this is part of that". Putting a dependency on top of
it produces a deadlock that no amount of careful status management can escape.

The refusal explains itself in the interface, and names the alternative:

> *VN-11 is part of VN-3, so it cannot depend on it. If VN-11 has to wait for
> something specific inside VN-3, point the dependency at that task instead.*

That sentence is doing real teaching work. It moves people from vague
containment thinking to the precise edge they actually meant.

### Guard 2 — no cycles

The existing system already checks this and the check does not change. A
dependency that would create a loop is refused with the path that would have
formed, so the person can see which existing edge to remove.

```
   Refused: VN-9 → VN-30 → VN-44 → VN-9
```

---

## 3. Position in a list never blocks anything

A version's children are written in a deliberate order, and that order is
useful. It is the author's advice about a sensible sequence, and it is what a
person or an agent reads to decide where to begin.

It is **not** a constraint, and the system never treats it as one.

```
   VERSION 1 of VN-3  Add comments
     1. VN-8   Comment model
     2. VN-9   Comment write path
     3. VN-10  Comment read path
     4. VN-11  Comment moderation
     5. VN-12  Show comments on the post page
```

Reading that list, positions 2 and 3 look sequential. They are not. The write
path and the read path both need the model from position 1, and neither needs
anything from the other, so once position 1 is done both can be worked on at
the same time by two different people.

If the numbering created blocking, the system would invent a constraint that
nobody stated, and the only way to express real parallel work would be to give
several children the same position, which is a worse way of saying nothing.

> **Two pieces of work are parallel exactly when neither needs anything the
> other produces. That is a fact about the work, and the system reads it from
> dependencies and from link states rather than from the numbering.**

---

## 4. Readiness, computed

A task is **ready** when nothing is standing in its way. Two separate things
can stand in the way, and they are shown differently because they mean
different things.

```
   BLOCKED                              WAITING ON CODE
   ───────                              ───────────────
   Something in depends_on is           A read, modify, or delete link points
   unfinished. A person wrote this      at a node that does not exist yet.
   edge down.                           Nobody wrote anything; the system
                                        noticed.

   ⛔ red. Names the blocking task.      ⚠ amber. Names the missing node.
```

The full computation for one task:

```
   ready  =  every task in depends_on is done
             AND every read/modify/delete link points at a node that exists
```

An example with both kinds at once:

```
   ┌──────────────────────────────────────────────────────────────┐
   │ VN-9   Comment write path                       ○ to do      │
   │ ⛔ blocked — VN-5 "Write current_user()" is not done          │
   │ ⚠ waiting — function app.auth.current_user does not exist yet │
   └──────────────────────────────────────────────────────────────┘
```

Both lines are about the same underlying situation, seen from two directions,
and that is deliberate rather than redundant. The first says who is responsible.
The second says what is missing. When the second appears **without** the first,
something important is being reported: the work needs code that nobody is
planning to write.

---

## 5. Dependencies should be suggested, not remembered

This is where the graph earns its place. Because every task names the nodes it
needs and the nodes it will create, the system can find the ordering that
already exists in the work and offer it.

```
   VN-9  Comment write path       read   ──► function app.auth.current_user   (missing)
   VN-5  Write current_user()     create ──► function app.auth.current_user   (pending)

                           the same name, one needs it, one makes it
                                            │
                                            ▼
   ┌────────────────────────────────────────────────────────────────────┐
   │  VN-9 needs current_user(), which VN-5 is planning to create.       │
   │  Add a dependency?     [ add it ]   [ not now ]                     │
   └────────────────────────────────────────────────────────────────────┘
```

The system offers; the person decides. It does not create the edge silently,
because a dependency changes what the board tells everybody else, and an
invented dependency is a lie that spreads.

Three cases produce a suggestion:

| Situation | Suggested edge |
|---|---|
| A needs a node that B plans to create | A depends on B |
| A modifies a node that B plans to delete | A depends on B, or the two of them need to talk |
| A and B both plan to create a node with the same name | Not a dependency. A duplicate warning, because one of them is probably unnecessary |

**Tradeoff.** Suggestions depend on people writing links, and on those links
using matching names. Where links are missing, no suggestion appears, and the
system stays silent rather than guessing. Silence is the right failure mode
here: a tool that invents dependencies from weak evidence teaches people to
ignore it.

---

## 6. Blocking rolls up, so nothing hides in the tree

A person looking at a high level card must be able to see that something inside
is stuck, without opening every level of the tree.

```
   ROOT BOARD
   ┌────────────────────────────────────────┐
   │ VN-3  Add comments      ● doing   3/5  │
   │ 🔴 1 blocked inside                     │  ← click to jump to VN-9
   └────────────────────────────────────────┘

   INSIDE VN-3
   ┌──────────────────────────────────────────────────────┐
   │ VN-9  Comment write path       ○ to do               │
   │ ⛔ blocked — VN-5 "Write current_user()"              │
   └──────────────────────────────────────────────────────┘
```

The parent shows a count and a way to jump. It is **not** itself marked blocked,
because that would be false: three of its five children can move right now.
Marking a parent blocked because one grandchild is waiting is how dependency
displays become noise that everybody ignores.

---

## 7. Dependencies that point at unusual places

**A dependency on a task nobody is doing.** VN-9 depends on VN-5, and VN-5 is
not referenced by any active version, so it is orphaned. VN-9 is still blocked,
correctly, and the chip says so plainly:

```
   ⛔ blocked — VN-5 "Write current_user()", which is not part of any active plan
```

That is exactly the situation somebody needs to know about, and the fix is
either to put VN-5 into a plan or to drop the dependency.

**A dependency on a task in a completely different part of the tree.** Fine,
and common. The board shows the blocker's breadcrumb so the person can see
where it lives:

```
   ⛔ blocked — VN-5  ▸ Authentication ▸ Session handling ▸ VN-5
```

**A dependency on a task that was deleted.** The edge goes with it. Task to
task links are real links, so a deleted task cannot leave a dangling
dependency, and a note is written on the other side saying the dependency
disappeared because the task was deleted.

---

## 8. Worked example

The starting graph has `User` and `Post`. Three pieces of work are planned.

```
   VN-1  Authentication            VN-2  Posts belong to users     VN-3  Add comments
     ├ VN-4  Password hashing        ├ VN-16 Add author to Post      ├ VN-8  Comment model
     ├ VN-5  Write current_user()    └ VN-17 Show author on page     ├ VN-9  Comment write path
     └ VN-6  Login page                                              ├ VN-10 Comment read path
                                                                     └ VN-12 Show comments
```

The links people wrote:

```
   VN-5   create  function app.auth.current_user
   VN-16  modify  class    app.models.Post
   VN-8   create  class    app.models.Comment
   VN-9   read    function app.auth.current_user     ← missing
   VN-9   read    class    app.models.Post
   VN-9   create  function app.services.createComment
   VN-9   modify  class    app.models.Comment
   VN-10  read    class    app.models.Comment
   VN-12  modify  function app.web.renderPost
```

What the system works out, with nobody writing a single dependency by hand:

```
   VN-9  needs current_user()      ── VN-5 will create it    ⇒ suggest VN-9 → VN-5
   VN-9  needs class Comment       ── VN-8 will create it    ⇒ suggest VN-9 → VN-8
   VN-10 needs class Comment       ── VN-8 will create it    ⇒ suggest VN-10 → VN-8
   VN-9  reads Post, VN-16 modifies Post                     ⇒ note, not a block
```

After the suggestions are accepted, here is what can be started today:

```
   READY NOW                        NOT YET
   ─────────                        ───────
   VN-4   Password hashing          VN-9   waits for VN-5 and VN-8
   VN-5   Write current_user()      VN-10  waits for VN-8
   VN-6   Login page                VN-12  waits for the read path to exist
   VN-8   Comment model
   VN-16  Add author to Post
```

Five tasks can start immediately, across all three areas of work, and nobody
had to reason about it. Notice also what did **not** happen: nobody wrote "Add
comments depends on Authentication", which would have stopped VN-8 and VN-12
for no reason at all.

---

## 9. Why dependencies do not point at versions

A reasonable idea is to let a dependency point at a specific version of a task,
or at one entry inside a version's child list, so that the record captures
exactly which piece of somebody else's approach you are waiting for.

The design does not do that, for one reason: **a version is somebody's current
description of how they will work, and they are allowed to replace it at any
time.** A pointer into a version means your dependency breaks whenever they
change their mind, which is precisely when you most need it to keep working.

Nothing is lost by pointing at the task instead, because the precise reason is
still recorded, just on the other side of the arrow:

```
   THE EDGE            VN-9  ──depends_on──►  VN-5
   THE REASON          VN-9 reads function app.auth.current_user
                       VN-5 creates function app.auth.current_user
```

The reason lives on the node links, which is where it can be checked. When VN-5
rewrites its approach, the dependency still holds if the new approach still
creates that function, and the system will point out that the reason has gone
if it does not.

The interface can still take you straight to the detail: a blocked chip links to
VN-5, and VN-5 always shows its active version, so the click through is one
step and never lands on something abandoned.

---

## 10. Costs and limits

**People still have to think.** Suggested dependencies only cover ordering that
shows up in the code. Ordering that comes from anything else, such as wanting a
feature flag reviewed before it goes live, has to be written by hand.

**Precise dependencies mean more edges.** Twenty small tasks with precise edges
produce more edges than four large ones with coarse edges. The relief is that
the edges are individually obvious, they roll up for display, and the level
board never shows more than one level of them at a time.

**The ancestor guard occasionally frustrates people.** Somebody genuinely wants
to say "this child cannot start until the parent's other work is done". The
right expression is a dependency on the specific sibling, and the refusal
message says so, but it does take a moment of learning.

The next file, [07 — Versions and alternatives](07-versions-and-alternatives.md),
covers what happens when there is more than one idea about how to do a task.
