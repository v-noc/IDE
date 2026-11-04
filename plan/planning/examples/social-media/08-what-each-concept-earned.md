# 08 — What Each Concept Earned

The design claims that every concept in it is necessary. This file checks that
claim against the example, by taking each concept away and describing what
breaks.

If removing something changes nothing, it should not exist. Everything below
changes something.

---

## Recursion — one entity that contains itself

**Take it away.** Fix the depth at two levels: tasks and subtasks.

**What breaks in this project.** VN-11 "Comment moderation" was one line in the
comments plan. Later it turned out to contain a real decision between a keyword
filter and a review queue, and it grew two children of its own.

```
   WITH RECURSION                  WITH A FIXED DEPTH
   ──────────────                  ──────────────────
   VN-3  Add comments              VN-3  Add comments
     VN-11 Moderation                VN-11 Moderation
       VN-22 Detect banned words        └── nowhere to put these
       VN-23 Hide a comment

                                   the options would be:
                                     promote VN-11 to a root task, breaking
                                     the connection to comments, or
                                     write both steps into its description,
                                     losing their status and their links
```

Neither workaround is acceptable, and the situation arose naturally from one
line of planning.

**Earned.**

---

## One parent per task

**Take it away.** Let a task be a child of several parents, so genuinely shared
work can sit in both places.

**What breaks.** Nothing visible on day one, which is why it is tempting. What
breaks is everything downstream. Progress counting has to deduplicate. Deleting a
parent cannot decide whether a child should survive. A task can become
unreachable from every plan while still existing, so an orphan concept has to be
invented, given a home on the root board, and explained to everybody.

In this example VN-12 "Show comments on the post page" is the shared-looking one:
comments need it, and a later post-page task will want it too. Under one parent
it lives inside VN-3, and the post-page task simply depends on it. That says
something truer than shared containment did — the post-page work is not
responsible for VN-12, it is waiting on it — and it costs one edge the system
already has.

**Earned**, and it removed three concepts (`is_shared`, `is_orphaned`,
`all_parents`) rather than adding one.

---

## Alternatives in the document, not in a second object

**Take it away.** Give every task a set of versions, one of them active.

**What breaks.** Less than the original design assumed. VN-11 had two real
approaches, and writing both into VN-11's document — chosen first, deferred
second, with the reasoning for each — records exactly what a version comparison
would have recorded.

What versions added on top of that was a state machine (draft, active,
superseded, discarded), a rule about which state counts for conflict detection,
an activation operation, and children that could be pointed at by two versions at
once. Every one of those is a place to be wrong, and none of them helped a reader
six months later more than a well-written section does.

**Cut, and not missed.** The rejected approach is still recorded, which was the
only thing genuinely at stake.

---

## The document on every task

**Take it away.** Keep only a description.

**What breaks.** VN-3's document contains the reasoning for a separate class,
the specific costs of the alternative, and an explicit note that the moderation
decision was pushed down rather than buried. None of that fits in a card
description, and all of it is what somebody joining the work needs.

**Earned**, with the honest note that a document is only as good as the person
writing it. The model provides the place; it cannot provide the discipline.

---

## Node links with modes

**Take them away.** Let a task point at nodes without saying what it does to
them — just "this work is connected to this node".

**What breaks.** Almost everything computed in this example:

```
   waiting on code                 gone — a bare pointer carries no direction
   suggested dependencies          gone — nothing knows who creates what
   verification of finished work   gone — no claim to check
   conflict detection              reduced to "two tasks are near this node"
   duplicate detection             gone
   ghost nodes on the canvas       gone
   the blast radius of VN-3        gone
```

Six of the eight most useful lists in [07](07-lookups.md) come from modes.

**Earned, decisively.**

---

## The `read` mode specifically

**Take it away.** Record only what work changes.

**What breaks.** VN-9's dependency on VN-5 came from a `read` link:
`createComment()` reads `current_user()`. Without read links, the system would
never notice that comments need something authentication is building, and
somebody would have to remember it.

The gentle notice in collision 3 also disappears: three tasks reading a class
that VN-16 is rewriting is worth one grey line, and it exists only because
reading is recorded.

**Earned.**

---

## Links that point at code which does not exist yet

**Take it away.** Only allow links to real nodes.

**What breaks.** At the moment planning happened, eight of the twelve
interesting nodes did not exist. Without pending links there would be no
readiness, no suggestions, no duplicate warning on `class Comment`, no ghosts on
the canvas, and no verification later.

The whole example is planned before it is built, which is what planning means.

**Earned.**

---

## One dependency edge, pointing at tasks, at any depth

**Take away the depth.** Only allow dependencies between root tasks.

**What breaks.** The one true statement is that VN-9 needs VN-5. The
root-level version of that statement is "comments depends on authentication",
which blocks VN-8, VN-11, VN-22, and VN-23 for no reason. Five of the six tasks
that could start on day one would show as blocked, and people would learn to
ignore the red chips.

**Earned.**

---

## The rule that position never blocks

**Take it away.** Make the child order sequential.

**What breaks.** VN-9 and VN-10 are positions 2 and 3 in the comments plan.
They both need the model from position 1, and neither needs anything from the
other, so two people can take them the same afternoon. A sequential reading
would block VN-10 behind VN-9 for no reason, and the only way to express real
parallelism would be to give several children the same position, which says
nothing at all.

**Earned.**

---

## Conflict resolution by deciding the order

**Take it away.** Leave only accept, resolve, and delegate.

**What breaks.** Collision 1 has no honest resolution. Both changes to
`createComment()` are needed, so nothing can be removed, and accepting would be
a lie because they genuinely interfere. The only real answer is that one goes
first, and without this option that agreement lives in somebody's memory instead
of on the board.

**Earned**, and it is the option that turns conflict detection from a
notification into a decision.

---

## Storing the decision but not the conflict

**Take it away.** Store conflicts as records.

**What breaks.** Collisions appear and vanish constantly here without anybody
touching a conflict: VN-11 finishing changes what VN-30 collides with, a reparse
changes which links resolve, and a scope narrowed in a document changes the whole
picture. Stored conflict records would have to be created and cleaned up on every
link edit, every status change, and every reparse, and any missed cleanup leaves
a warning about a situation that no longer exists.

Computing them means the display is always right and nothing can go stale.

**Earned.**

---

## `affects` meaning the node, not its contents

**Take it away.** Let a task write `affects class Comment` whenever it changes
anything inside `Comment`.

**What breaks.** VN-8 and VN-22 both work inside `class Comment` — one creating
the model, one adding a check to `createComment`. Under the loose reading, both
would claim to affect the class, and the system would report a collision that
does not exist.

Now generalise that. Almost all work adds or changes a method, so almost every
class two people are working near would show a permanent conflict:

```
   LOOSE READING                          THIS DESIGN
   ─────────────                          ───────────
   VN-8   affects class Comment           VN-8   create function Comment.validate
   VN-22  affects class Comment           VN-22  affects function createComment

   ⚑ conflict — but there is none         no conflict, and both still appear
                                          when you ask what touches Comment
```

Conflict detection would not degrade gracefully; it would become noise, and
noise gets clicked past. Everything in [06](06-conflicts.md) depends on the
warnings being rare enough to read.

**Earned, and load bearing.**

---

## Severity coming from task status

**Take it away.** Treat every link as equally serious.

**What breaks.** VN-30 "Rate limiting" sat untouched in the backlog for weeks
while it declared `affects createComment()`. Under a flat reading it would have
been arguing with VN-11 that whole time, over a plan nobody had committed to.

The alternative that suggests itself — a `provisional` flag on each link — is
worse than it looks. It is a second record of "how serious is this", maintained
by hand, drifting out of step with the status field that people already update
because the board depends on it.

**Earned**, with one honest gap: a task worked on from the backlog warns nobody.
That is a housekeeping list, not a new field.

---

## The board showing one level

**Take it away.** Show every task on one board.

**What breaks.** Fifteen tasks in a project this small. The root board shows
four cards, and each level below shows between two and five. A flat board would
show fifteen cards where four of them are the actual project and eleven are
implementation detail, which is precisely the outcome the recursive model is
otherwise accused of producing.

**Earned**, and it is what makes recursion usable rather than overwhelming.

---

## What was removed, and stayed removed

Four things were considered and cut. This project never needed any of them:

```
   blocked_by as a second edge     one edge, read from both ends, never disagreed
   related_to                      every "related" pair here was already visible
                                   through a shared node or a shared parent
   references, separate from context   nobody could have said which to use
   a duplicates relationship       the duplicate in 06 was found by the link
                                   index, and merging is housekeeping
```

Their absence produced no gap anywhere in this example.

---

## The scoreboard

```
   CONCEPT                                     VERDICT
   ───────                                     ───────
   recursion                                   earned
   one parent per task                         earned — load bearing
   task document                               earned
   node links with modes                       earned — decisively
   read mode                                   earned
   affects means the node, not its contents    earned — load bearing
   links to code that does not exist yet       earned
   dependencies at any depth                   earned
   position never blocks                       earned
   resolution by ordering                      earned
   decisions stored, conflicts computed        earned
   severity from task status                   earned
   one level per board                         earned

   versions                                    cut, not missed
   shared children / orphans                   cut, not missed
   a vague "connected to this node" pointer    cut, verified nothing
   a provisional flag on links                 cut, status already says it
   blocked_by as a second edge                 cut, not missed
   related_to                                  cut, not missed
   references                                  cut, not missed
   duplicates                                  cut, not missed
```

Back to the [design files](../../README.md).
