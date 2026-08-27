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
        │ affects                   │ affects
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
                 read      create     affects     delete
             ┌──────────┬──────────┬──────────┬──────────┐
      read   │  quiet   │  quiet   │  watch   │  watch   │
             ├──────────┼──────────┼──────────┼──────────┤
    create   │  quiet   │ DUPLICATE│ conflict │ conflict │
  T          ├──────────┼──────────┼──────────┼──────────┤
  H  affects  │  watch   │ conflict │ CONFLICT │ SEVERE   │
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

There is no vague mode to exempt. Every link states one of four things, and the
matrix has an answer for each pair.

### Why "watch" exists as its own level

A reader under a writer is worth a quiet mention and nothing more.

```
   VN-16  Add author to Post      affects ──► class Post
   VN-9   Comment write path      read    ──► class Post

   VN-9 is reading a class that is about to change. Its plan may be based on
   an old shape. Nobody is blocked. Nobody needs to negotiate.
```

Making this a full conflict would mean almost every task conflicts with almost
every other one, since reading is common. Ignoring it completely would lose a
real signal, which is that a plan was written against code that is about to
change underneath it.

---

## 3. Severity comes from task status

The mode matrix says how two intentions interact. It does not say how much
either intention should be believed. A link on a task somebody is actively
working on is a claim. The same link on a half-written idea in the backlog is a
thought.

**Task status already carries that difference**, so severity reads it directly:

| Situation | Warning |
|---|---|
| Two ready or in-progress tasks affect the same node | **conflict** — loud |
| One ready, one draft | **watch** — quiet |
| Two drafts | nothing |

"Draft" means the backlog column — the one carrying `is_backlog`. Promoting a
task out of the backlog is the moment its plan stops being an idea and starts
being a claim, which is exactly when other people need to hear about it.

### Why not a flag on the link

The obvious alternative is a `source` or `typed / inferred` field on each link,
so a link can mark itself provisional.

That would be a second, parallel notion of "how serious is this", maintained by
hand, drifting out of step with the status field that already exists and is
already kept current because the board depends on it. Nobody updates a link's
provisional flag when they start work; everybody moves the card.

> **Use the state people already maintain. Do not invent a second one that
> records the same thing worse.**

**Known gap, accepted.** A task parked in draft forever, with links, warns
nobody — and if it is genuinely being worked on from the backlog, the warning
that should have fired never does. The answer is a housekeeping list — *draft
tasks with links, unchanged for N days* — rather than a new field. A list can be
ignored without corrupting anything; a stale flag cannot.

---

## 4. What else is excluded

Two more scope rules keep the signal honest.

- **Finished work stops colliding.** A task in a done column has finished
  writing, so it leaves collision detection. What it did is now history, and
  history belongs in commits.
- **The strongest link per task per node counts once.** If a task both reads and
  affects a class, it counts once, as a writer.

The second rule matters for the rollup. A parent's effective links include every
descendant's links, so a parent can appear to conflict with its own child if
nobody is careful. The rule is that **a task never conflicts with its own
ancestors or descendants**, because a family working on the same node is the
normal case rather than a problem.

Derived containment is excluded for the same reason. When VN-8 creates
`Comment.validate`, `class Comment` shows up as touched by VN-8 — but that is
containment, not a claim about the class, so it never triggers a warning. Only
an explicit `affects class Comment` does. This is what stops every class in the
codebase from being permanently amber, and it is why [05](05-graph-links.md) §3
insists that `affects` means the node itself.

---

## 5. Where a conflict is visible

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
one intends to do, and the two resolutions.

---

## 6. The two ways a conflict ends

### Decide the order

This is the most common and most useful resolution. Both pieces of work are
correct and both are needed. They simply must not happen at the same time.
Choosing an order turns a collision in space into a sequence in time, using the
one ordering edge the system already has.

```
   BEFORE                                AFTER
   ──────                                ─────
   VN-11 affects createComment()          VN-11 ──depends_on──► VN-30
   VN-30 affects createComment()

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

### Why only two

Two other outcomes were on the table and were cut, because neither had a
mechanism behind it.

**Changing the work so the links no longer overlap** is not a decision the
system needs to record. Somebody narrows a scope or splits a function, the links
stop overlapping, and the conflict disappears on its own — it was never stored.
The reasoning belongs in the task's document, where a reader will actually find
it.

**Delegating the decision to somebody else** was a record with nobody attached
and nothing that happened next. When there is a real assignment model, this can
come back as an assignment. Until then it is a note that looks like a workflow.

`ordered` writes a real dependency edge. `accepted` silences a warning under a
stated condition. Both change what the system does. That is the bar.

---

## 7. The best conflict is the one found before anybody writes code

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

The resolution is usually a merge: one task is deleted, or one is reparented
under the other, and the surviving task inherits the useful parts of both
documents.

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
       affects  function app.services.createComment
   Nothing else touches it. No warning.

   Tuesday
   ───────
   Someone plans VN-11 "Comment moderation", and records:
       affects  function app.services.createComment

   Immediately, on both cards and on the node:
       ⚑ contested — createComment() is being affected by 2 open tasks

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
