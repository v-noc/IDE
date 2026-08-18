# 08 — Conflicts and Concurrency

Two people, or two agents, working in the same place at the same time is the
most expensive thing that happens in software, and every tool finds out about
it too late. Version control finds out at merge time. Code review finds out
after both sides are written. A task board never finds out at all.

Because every task in this system names the nodes it intends to touch, this one
can find out **at planning time**, before anybody has typed a line.

---

## 1. What a conflict actually is

A conflict is not a merge failure. It is two pieces of open work that both
intend to write the same node.

```
   function  app.services.createComment
        ▲                          ▲
        │ modify                   │ modify
        │                          │
   VN-11  Comment moderation   VN-30  Rate limiting
   ○ to do                     ● in progress
```

Nothing is broken. No file has changed. But two people are about to rewrite the
same function without knowing about each other, and one of them is going to
have a bad afternoon.

The system computes this from the links it already has, and it computes it
fresh every time somebody looks. **The collision is never stored.** What gets
stored is only what a human decided to do about it, which is covered in
section 5.

---

## 2. The mode matrix

Not every overlap matters, and treating them all the same would produce noise
that people learn to ignore. The mode on each link decides how serious the
overlap is.

```
                            THE OTHER TASK
                 read      create     modify     delete
             ┌──────────┬──────────┬──────────┬──────────┐
      read   │  quiet   │  quiet   │  watch   │  watch   │
             ├──────────┼──────────┼──────────┼──────────┤
    create   │  quiet   │ DUPLICATE│ conflict │ conflict │
  T          ├──────────┼──────────┼──────────┼──────────┤
  H  modify  │  watch   │ conflict │ CONFLICT │ SEVERE   │
  I          ├──────────┼──────────┼──────────┼──────────┤
  S  delete  │  watch   │ conflict │ SEVERE   │ duplicate│
             └──────────┴──────────┴──────────┴──────────┘
```

| Level | Meaning | How it is shown |
|---|---|---|
| quiet | Two readers, or unrelated. Not worth saying anything | nothing |
| watch | One side writes, the other reads. The reader's assumptions may expire | small grey note on the reading task |
| duplicate | Both plan to create the same thing, or both plan to delete it | amber, with "one of these is probably unnecessary" |
| conflict | Both plan to write, in ways that will interfere | amber on both cards and on the node |
| severe | One deletes what another is changing | red, because one side's work will simply vanish |

The `about` mode never produces anything. Anchors are vague by design, and
warning on vagueness would fill the screen with meaningless amber.

### Why "watch" exists as its own level

A reader under a writer is worth a quiet mention and nothing more.

```
   VN-16  Add author to Post      modify  ──► class Post
   VN-9   Comment write path      read    ──► class Post

   VN-9 is reading a class that is about to change. Its plan may be based on
   an old shape. Nobody is blocked. Nobody needs to negotiate.
```

Making this a full conflict would mean almost every task conflicts with almost
every other one, since reading is common. Ignoring it completely would lose a
real signal, which is that a plan was written against code that is about to
change underneath it.

---

## 3. What counts, and what does not

Scope rules keep the signal honest. A conflict is only computed between:

- **open work.** A task in a done column has finished writing, so it stops
  taking part in collision detection. What it did is now history, and history
  belongs in commits.
- **active versions.** A draft version is a thought, not an intention. Its
  links do not collide with anything. This lets people write two competing
  approaches without the two of them fighting each other on screen.
- **the strongest link per task per node.** If a task both reads and modifies a
  class, it counts as a modifier, once.

The last rule matters for the rollup. A parent's effective links include every
descendant's links, so a parent can appear to conflict with its own child if
nobody is careful. The rule is that **a task never conflicts with its own
ancestors or descendants**, because a family working on the same node is the
normal case rather than a problem.

---

## 4. Where a conflict is visible

The same computed fact appears in four places, all reading one summary rather
than each working it out again.

```
   ON THE NODE, on the canvas
   ┌────────────────────────┐
   │ ƒ createComment()   ⚑2 │   amber badge, click to see who
   └────────────────────────┘

   ON EACH TASK CARD
   ┌────────────────────────────────────────────┐
   │ VN-11  Comment moderation      ○ to do     │
   │ ⚑ contested — createComment() also in VN-30│
   └────────────────────────────────────────────┘

   IN THE SIDEBAR, as a list of contested nodes ranked by how many tasks want them

   IN THE TASK DETAIL PANEL, on the affected node row itself
```

Clicking any of them opens the same small panel showing both tasks, what each
one intends to do, and the four resolutions.

---

## 5. The four ways a conflict ends

### Decide the order

This is the most common and most useful resolution. Both pieces of work are
correct and both are needed. They simply must not happen at the same time.
Choosing an order turns a collision in space into a sequence in time, using the
one ordering edge the system already has.

```
   BEFORE                                AFTER
   ──────                                ─────
   VN-11 modify createComment()          VN-11 ──depends_on──► VN-30
   VN-30 modify createComment()

   ⚑ CONFLICT                            ⏭ SEQUENCED
                                         VN-30 goes first.
                                         VN-11 is now blocked, everywhere,
                                         with a reason attached.
```

The dependency is a real edge, so the board, the rollups, and the readiness
calculation all reflect it immediately, and nobody has to remember the
agreement. The conflict decision record keeps the *why*, which a bare
dependency edge could never explain on its own.

Once the edge exists, the pair is shown as sequenced rather than as a live
conflict. They still touch the same node; they just cannot collide any more.

### Accept it

The two pieces of work touch the same node in ways that will not actually
interfere, most often two functions being added to the same file.

```
   ⚑ accepted by Yared — "different functions, same file, no overlap"
```

The warning goes quiet and stays quiet unless the links change. If either side
later adds a link that makes the situation worse, the decision is shown as no
longer covering the current situation, and the warning comes back.

### Resolve it by changing the work

Somebody narrows a scope, moves a change into the other task, or splits a
function in two. The links stop overlapping, and the conflict disappears on its
own because it was never stored. The decision record explains what was done, so
the next person understands why the shape of the work is what it is.

### Delegate it

The two people involved cannot settle it. The record names who is being asked
to decide, and the conflict stays visible until they do.

This is the seam that a future agent workflow would use. An agent that finds
itself planning work over a node another agent is rewriting has somewhere to
put the question, and a human has somewhere to answer it. Nothing about that
workflow is designed here; the point is that the model can hold the situation.

---

## 6. The best conflict is the one found before anybody writes code

The strongest signal this system produces does not need any code to exist yet.

```
   pending create ──► class app.models.Comment  ── VN-8   Comment model
   pending create ──► class app.models.Comment  ── VN-44  Comment storage

   ⚑ DUPLICATE
     Two tasks plan to create the same class. Neither has been written.
```

Two people planned the same class in two different parts of the tree, probably
in different weeks, probably without knowing about each other. In every other
tool this is found in code review, or never. Here it is found while both are
still just text.

The resolution is usually a merge: one task is deleted, or one becomes a child
of the other, and the surviving task inherits the useful parts of both
documents.

---

## 7. Relationship to the existing hot node idea

The current system already has something close to this: a node is **hot** when
two or more open tasks anchor to it. That idea is kept, and this is a sharper
version of it.

```
   TODAY                              WITH MODES
   ─────                              ──────────
   two tasks anchored here            two tasks intend to MODIFY this
   ⇒ hot                              ⇒ conflict

                                      one modifies, two read
                                      ⇒ watch, quieter

                                      two anchored, no links written
                                      ⇒ still hot, same as today
```

Nothing regresses. A task with only anchors and no links still contributes to
the hot count exactly as it does now, so the existing canvas badges and the
sidebar blockers list keep working while links are gradually adopted. Tasks
that have links get the sharper signal.

---

## 8. What this cannot do, stated plainly

**It only knows what people wrote down.** Two tasks that will collide but never
recorded links produce no warning. The system fails silently rather than
guessing, which is the right direction to fail in, but it does mean coverage
depends on habit. The mitigation is to make links cheap to add: created
automatically when a task is made from a node, suggested from callers and
callees, and rolled up so only leaves need them.

**It works at node granularity, not line granularity.** Two tasks changing
different parts of the same big function will be reported as a conflict when
they might be fine. That is why `accepted` exists and why it takes one click.

**It sees intentions, not the working tree.** Somebody might already have half
the work uncommitted on their machine. The planning layer cannot know. What it
can do is compare links against commits after the fact and point out where
reality diverged from the plan.

**A reparse can move the ground.** Nodes disappear and are recreated as files
change, so a conflict can appear or vanish because of a rename. Since nothing
is stored, the display simply corrects itself on the next read, and no stale
warning survives.

---

## 9. Walked through, end to end

```
   Monday
   ──────
   Yared plans VN-30 "Rate limiting", and records:
       modify  function app.services.createComment
   Nothing else touches it. No warning.

   Tuesday
   ───────
   Someone plans VN-11 "Comment moderation", and records:
       modify  function app.services.createComment

   Immediately, on both cards and on the node:
       ⚑ contested — createComment() is being modified by 2 open tasks

   Tuesday afternoon
   ─────────────────
   They open the conflict panel. Both changes are needed. Rate limiting is
   nearly finished, moderation has not started.

   They choose:  decide the order.

       VN-11 ──depends_on──► VN-30
       reason: "rate limiting lands first, moderation builds on top"

   Now:
       VN-11 shows  ⛔ blocked — waiting for VN-30
       the node shows  ⏭ sequenced, 2 tasks
       the board rollup on the parent shows one blocked task inside
       nobody has to remember anything

   Friday
   ──────
   VN-30 moves to done.
   VN-11 becomes ready, everywhere, with no further action, because
   readiness was never stored in the first place.
```

The next file, [09 — Architecture](09-architecture.md), explains how all of this
derivation is made fast enough to run on every read.
