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

## Versions — many approaches, one active

**Take them away.** One plan per task, edited in place.

**What breaks.** The comments task had two genuinely different approaches, and
the comparison in [04](04-alternative-versions.md) is what made the choice
obvious: one approach adds a class nothing else touches, the other rewrites a
class three other tasks are already involved with.

Without versions, that comparison happens in somebody's head or in a document
nobody can find, and the rejected approach disappears entirely. Six months later
the question "why didn't we just store comments in the post?" has no recorded
answer.

**Earned.**

---

## Reference, not ownership — versions point at children

**Take it away.** Let the approach own its steps.

**What breaks.** In [04](04-alternative-versions.md), v2 was activated while
VN-8 was already finished and VN-9 was half written. With ownership, activating
v2 forces a choice between deleting finished work, showing work that belongs to
an abandoned approach, or moving work across and inventing an intention nobody
expressed.

With reference, nothing happens at all. VN-8 stays done, gains a chip saying it
is not in any active plan, and reports that the class it created is still in the
codebase.

**Earned, and this is the load-bearing one.** It is the reason changing your
mind is cheap in both directions.

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

**Take them away.** Keep anchors, which say only "this work is around here".

**What breaks.** Almost everything computed in this example:

```
   waiting on code                 gone — anchors carry no direction
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

**What breaks.** In [04](04-alternative-versions.md) the active version changed
twice. Each switch changed which links count, so collisions appeared and
vanished. Stored conflict records would have to be created and cleaned up on
every activation, on every link edit, and on every reparse, and any missed
cleanup leaves a warning about a situation that no longer exists.

Computing them means the display is always right and nothing can go stale.

**Earned.**

---

## Anchors, kept alongside links

**Take them away.** Say everything with typed links.

**What breaks.** VN-3 was created with only `⚓ folder app/`, before anybody knew
what it would touch. Forcing a mode at that moment means guessing, and a guess
recorded as `modify` would produce a false collision.

Anchors are how work starts. Links are how it gets specific.

**Earned**, though it is the smallest margin in this file. The distinction has
to be explained once, and the payment for that is that vague early work is
recorded honestly instead of being recorded wrongly.

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
   versions                                    earned
   reference not ownership                     earned — load bearing
   task document                               earned
   node links with modes                       earned — decisively
   read mode                                   earned
   links to code that does not exist yet       earned
   dependencies at any depth                   earned
   position never blocks                       earned
   resolution by ordering                      earned
   decisions stored, conflicts computed        earned
   anchors alongside links                     earned — narrowly
   one level per board                         earned

   blocked_by as a second edge                 cut, not missed
   related_to                                  cut, not missed
   references                                  cut, not missed
   duplicates                                  cut, not missed
```

Back to the [design files](../../README.md).
