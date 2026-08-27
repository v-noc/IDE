# 05 — Dependencies and Readiness

Fifteen tasks exist across three trees. Nobody has written a single dependency
by hand. This file shows what the system works out from the links alone, which
dependencies get suggested, and exactly what can be started on day one.

---

## Step 1 — What the links already say

Every task named the nodes it needs and the nodes it will create. Lining those
up produces the ordering that is already implied by the work.

```
   NEEDS SOMETHING THAT DOES NOT EXIST YET        WHO PLANS TO CREATE IT
   ────────────────────────────────────────       ──────────────────────
   VN-6   reads   hash_password()                 VN-4   ✓ already done
   VN-9   reads   current_user()                  VN-5
   VN-9   reads   class Comment                   VN-8
   VN-10  reads   class Comment                   VN-8
   VN-12  reads   listComments()                  VN-10
   VN-22  changes createComment()                 VN-9
   VN-23  changes renderPost()                    exists already
   VN-30  changes createComment()                 VN-9
```

Every row in the left column produces an amber **waiting on code** chip
immediately, with no coordination between anybody.

```
   ┌──────────────────────────────────────────────────────────┐
   │ VN-9   Comment write path                    ○ to do     │
   │ ⚠ waiting — function app.auth.current_user does not exist │
   │ ⚠ waiting — class app.models.Comment does not exist       │
   └──────────────────────────────────────────────────────────┘
```

That much is free. It requires nobody to know that another tree exists.

---

## Step 2 — The suggestions

The right column is what turns waiting into blocking. Because the system knows
who plans to create each missing node, it can offer the dependency.

```
   ┌────────────────────────────────────────────────────────────────────┐
   │  VN-9 needs current_user(), and VN-5 plans to create it.            │
   │  VN-9 needs class Comment, and VN-8 plans to create it.             │
   │                                       [ add both ]   [ not now ]    │
   └────────────────────────────────────────────────────────────────────┘
```

Accepting them all produces this set of edges:

```
   VN-9   ──depends_on──►  VN-5      needs current_user()
   VN-9   ──depends_on──►  VN-8      needs class Comment
   VN-10  ──depends_on──►  VN-8      needs class Comment
   VN-12  ──depends_on──►  VN-10     needs listComments()
   VN-22  ──depends_on──►  VN-9      changes createComment(), which VN-9 creates
   VN-30  ──depends_on──►  VN-9      changes createComment(), which VN-9 creates
```

Six edges, and every one of them has a reason recorded on both ends. Nobody had
to remember anything, and nobody wrote "comments depends on authentication",
which would have been the coarse and mostly wrong form of one of these.

Notice which edge did **not** get created:

```
   VN-6 reads hash_password(), which VN-4 creates.
   VN-4 is already done, so the node exists.
   No suggestion. No dependency. VN-6 is simply ready.
```

The system only suggests ordering that still matters.

---

## Step 3 — The dependency picture

```
                    ┌── VN-4  Password hashing  ✓ done
   AUTH             │
                    ├── VN-5  current_user()  ─────────────┐
                    └── VN-6  Login page                   │
                                                           │
   POSTS            ┌── VN-16 author_id field              │
                    └── VN-17 show author                  │
                                                           ▼
   COMMENTS         ┌── VN-8  Comment model ──────────► VN-9  write path
                    │            │                          │
                    │            └──────────► VN-10 read path
                    │                              │        │
                    │                              ▼        │
                    │                        VN-12 show comments
                    │                                       │
                    └── VN-11 moderation                    │
                          ├── VN-22 detect banned words ◄───┤
                          └── VN-23 hide a comment          │
                                                            │
   OTHER            VN-30 Rate limiting ◄───────────────────┘
```

Two things to notice about the shape.

**Dependencies cross trees freely.** VN-9 in the comments tree waits for VN-5 in
the authentication tree. That is three levels deep on one side and two on the
other, and it is exactly as precise as the real reason.

**Whole trees are not blocked.** The authentication tree contains the thing
comments needs, but only one comments task waits for it. VN-8, VN-11, and the
whole moderation subtree proceed regardless.

---

## Step 4 — What can be started today

```
   READY NOW                              WAITING
   ─────────                              ───────
   VN-5   Write current_user()            VN-9    ⛔ VN-5, VN-8
   VN-6   Login page                      VN-10   ⛔ VN-8
   VN-8   Comment model                   VN-12   ⛔ VN-10
   VN-16  Add an author_id field          VN-22   ⛔ VN-9
   VN-17  Show the author                 VN-23   ⚠ waiting on the read path
   VN-11  Comment moderation (planning)   VN-30   ⛔ VN-9
```

Six tasks can start immediately, spread across all three trees. Five people
could work in parallel on day one without talking to each other, and the sixth
could plan moderation.

That parallelism was never declared anywhere. Nobody marked tasks as parallel,
nobody grouped them into phases, and nobody drew a chart. It is simply what is
left over once the real ordering is known.

---

## Step 5 — What the board shows

```
   ROOT BOARD
   ┌──────────────────────┬────────────────────────┬─────────────┐
   │ TO DO                │ IN PROGRESS            │ DONE        │
   ├──────────────────────┼────────────────────────┼─────────────┤
   │ VN-3  Add comments   │ VN-1  Authentication   │             │
   │ 0 of 5 · ▸ 5         │ 1 of 3 · ▸ 3           │             │
   │ 🔴 4 blocked inside   │                        │             │
   │                      │ VN-2  Posts belong to  │             │
   │ VN-30 Rate limiting  │ users  0 of 2 · ▸ 2    │             │
   │ ⛔ VN-9               │                        │             │
   └──────────────────────┴────────────────────────┴─────────────┘
```

VN-3 shows `4 blocked inside` and is not itself marked blocked, which is
correct: VN-8 and VN-11 can both start right now. A parent marked blocked
because one grandchild is waiting would be false, and a board full of false red
chips is a board nobody reads.

Clicking the red marker goes straight to the blocked tasks rather than making
somebody hunt through three levels.

---

## Step 6 — Watching the chain unblock

VN-5 and VN-8 are picked up and finished on the same afternoon.

```
   VN-5 moves to done
     app.auth.current_user appears in the graph
     VN-5's create link turns from pending to fulfilled
     VN-5 reads: done · verified

   VN-8 moves to done
     app.models.Comment appears in the graph
     VN-8 reads: done · verified

   IMMEDIATELY, computed, with nobody doing anything:
     VN-9  loses both blockers and both amber chips        ⇒ READY
     VN-10 loses its blocker                               ⇒ READY
     VN-3's rollup drops from 4 blocked inside to 2
```

Nothing was updated. No flags were cleared. Readiness was never stored in the
first place, so the correct answer simply appears the next time anybody looks.

The same is true in reverse. If VN-5 were reopened tomorrow, VN-9 would become
blocked again on the next read, with no chance of a stale chip on either side.

---

## What one coarse dependency would have cost

Worth showing, since it is the habit this design is trying to replace.

```
   THE COARSE EDGE                        WHAT IT COSTS
   ──────────────────                     ─────────────
   VN-3 ──depends_on──► VN-1              VN-8, VN-11, VN-22, VN-23 all wait
   "comments needs authentication"        for password hashing and a login
                                          page they do not use.

                                          Five of the six tasks that could
                                          start today would show as blocked.

                                          People learn that red chips are
                                          usually wrong, and stop reading them.
```

The precise form needs more edges, and every one of those edges is
individually obvious, suggested by the system, and traceable to a node.

Next: [06 — Conflicts](06-conflicts.md).
