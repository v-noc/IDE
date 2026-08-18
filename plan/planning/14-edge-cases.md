# 14 — Edge Cases

This file tries to break the model. Each case states the situation, what the
model does, and an honest verdict: whether the answer is genuinely good, or
merely acceptable, or a known weakness.

A model that only works in the happy path is not a model. The point of this
file is that when the answer is awkward, the response is to reconsider the
shape rather than to add another special rule.

---

## 1. A task has no plan at all

Somebody creates "Fix the comment spacing bug" and never writes anything else.

**What happens.** The task is created with one version that is active and
almost empty: no document, no links, no children. It sits on the board, it can
be moved between columns, it can be finished.

**Verdict: good.** There is no such thing as an unplanned task in the model,
which removes a whole category of special cases. A task with nothing written
down is simply a task whose version is empty, and it behaves like every other
task. Small work stays small.

---

## 2. A task has several versions

**What happens.** One is active. The others are drafts, superseded, or
discarded. The interface shows a switcher, and any non-active version is read
behind a warning band saying it is not the plan.

**Verdict: good**, with one interface requirement that cannot be skipped. If
the band is missing, somebody will edit a draft believing it is the plan. That
is why [11](11-ui-surfaces.md) treats it as a rule rather than a nicety.

---

## 3. A version is abandoned

**What happens.** A draft that is dropped becomes `discarded`. A version that
was active and got replaced becomes `superseded`. Neither is deleted.

The distinction matters because a superseded version has code in the repository
that came from it, and a discarded one does not. Somebody reading the history
needs to tell those apart.

**Verdict: good.** Keeping rejected ideas is one of the most valuable things a
planning tool can do, and it costs almost nothing.

---

## 4. The active version changes

**What happens.** The task's pointer moves, the old version is marked
superseded, and a note is written. Nothing else is performed. Everything else
is computed afterwards: the board level lists different children, orphans
appear, conflicts recompute.

**Verdict: good, and this is the case the whole model was shaped around.**
Because a version refers to children rather than owning them, changing your
mind is a pointer move rather than a migration.

---

## 5. A child was finished, and then the version changed

VN-8 "Comment model" is done. The new approach does not use it.

**What happens.** Nothing to VN-8. It stays done, with its history. It gains a
grey chip saying it is not part of any active plan, and the panel can say
something more useful than that:

```
   ⌫ VN-8 is not part of any active plan
     it created:  class app.models.Comment   ← still in the codebase
     nothing in any active plan mentions this class
```

**Verdict: good, and better than expected.** Because finished work names the
nodes it created, abandoning an approach surfaces the code left behind. An
ordinary board would simply lose track of it.

---

## 6. A child affects a node that another task is modifying

**What happens.** Both tasks link the node with a write mode, so the pair is
contested. Both cards show it, the node shows it, and four resolutions are
offered, one of which creates a real dependency.

**Verdict: good.** This is the feature, not an edge case.

---

## 7. Two tasks modify the same node, and both are already in progress

**What happens.** Same as above, except neither can simply wait. The likely
resolution is `accepted` with a reason, or `resolved` by narrowing one scope.

**Verdict: acceptable.** The system reports the situation accurately and
records the decision. It cannot merge anybody's code, and it does not pretend
to. Its contribution is that both people know on the day rather than at merge
time.

---

## 8. A task is blocked by another task

**What happens.** One stored edge, computed blocking, chips on both sides with
breadcrumbs, and rollup to the parent so nothing hides in the tree.

**Verdict: good.**

---

## 9. A task deep in one tree is blocked by a task deep in another tree

VN-9, three levels inside Comments, needs VN-5, two levels inside
Authentication.

**What happens.** The edge is allowed, because dependencies connect tasks at
any depth. Both chips carry breadcrumbs so the other side can be found. Both
parents show a rollup marker.

**Verdict: good.** This is exactly the precision the recursive model buys, and
it is the case a task-level-only dependency system handles badly, since it
would force "Comments depends on Authentication" and stop four unrelated tasks.

---

## 10. A graph node is deleted, and a link still points at it

**What happens.** The link keeps its name snapshot and becomes `unresolved`. It
displays as a warning that still reads sensibly, with three actions: point at
another node, remove the link, or change it into a `delete` link, which may be
exactly what the work was.

**Verdict: good.** This is why links are soft references with snapshots rather
than hard database links, and the current anchor design already proved the
approach.

---

## 11. A node still exists but has changed completely

The function is still called `createComment`, but it was rewritten and now does
something else entirely.

**What happens.** Nothing. The link still resolves, because the node id is the
same, and the system has no way to know the meaning changed.

**Verdict: a real weakness, and worth naming.** The system tracks identity, not
meaning. The partial defence is that a rewrite is itself somebody's work, and if
that work recorded a `modify` link on the node, then anybody else linking it
sees a contested or watch marker. Where the rewrite happened with no task at
all, the planning layer cannot know. This is the honest limit of planning on
top of structure rather than on top of behaviour.

---

## 12. A task is split into several tasks

**What happens.** The split operation creates the new tasks as children, moves
selected links down to them, and writes a note. The original task keeps its
identity, its key, its dependencies, and its place in every parent's list.

**Verdict: good**, and notably better than a flat model, where splitting either
loses the original or creates a fake parent. Here the original simply gains
children, which is a thing every task can do.

---

## 13. A task is duplicated by mistake

Two people file "Add comment moderation" a week apart.

**What happens.** If both wrote links, the system spots it before either starts:
two tasks planning to create the same node produce a duplicate warning, which is
the strongest early signal in the design.

If neither wrote links, nothing is detected automatically, and somebody notices
by reading. Merging is manual: point the survivor's version at whatever children
the duplicate had, copy anything useful out of its document, delete the
duplicate with a note saying where it went.

**Verdict: good when links exist, acceptable when they do not.** There is no
`duplicates` relationship, because marking a duplicate is housekeeping rather
than a fact worth modelling.

---

## 14. A plan creates a node that does not exist yet

**What happens.** A `create` link is stored by name and kind with no id, shown
as pending, drawn on the canvas as a dashed ghost, indexed by name so duplicates
are found, and bound to a real node when one appears with a matching name and
kind.

**Verdict: good, and it is the most distinctive thing here.** The plan is
visible in the graph before the code exists.

The known imperfection: binding by name is a guess. An exact match binds
automatically, anything else is offered as a suggestion, and a mismatch leaves
the link pending with a `done · unverified` marker on the task. That is a
visible imperfection, which is the right kind.

---

## 15. One node is affected by many tasks

A popular class is linked by fifteen tasks.

**What happens.** The node summary lists them grouped by mode, so the important
distinction is immediate: three intend to modify it, twelve only read it. The
badge shows the write count, not the total, because fifteen is noise and three
is a decision.

**Verdict: good.** Grouping by mode is what stops popular nodes from being
permanently amber.

---

## 16. One task affects many nodes

A big refactor touches sixty nodes.

**What happens.** The links are listed, grouped by kind and mode, and collapsed
by default with counts. Rollup means the parent card can say "modifies 60
nodes" without listing them.

**Verdict: acceptable, with a nudge.** Sixty affected nodes on one leaf task
usually means the task should have children. The interface can say so as a hint,
but it must not refuse, because some refactors genuinely are one sweep.

---

## Four more the recursive model invites

### 17. The same task appears under two parents

**What happens.** Allowed, and deliberately so. Shared work is real. The task
shows a `shared` chip naming its parents, and progress counting deduplicates so
it is never counted twice.

**Verdict: good**, with a caution: heavy sharing turns the tree into a web, and
the interface should show sharing clearly enough that people notice when they
are doing it a lot.

### 18. Somebody tries to make a cycle

Either by putting a task inside itself through some path, or by adding a
dependency that loops.

**What happens.** Both are refused with the path that would have formed. The
containment check and the dependency check are separate, because they are
separate graphs.

**Verdict: good.** The existing system already refuses dependency cycles, and
containment gets the same treatment.

### 19. A parent is deleted while its children are still wanted

**What happens.** Children are never deleted with a parent. Any child with no
remaining parent becomes a root task, where it is visible on the root board.

**Verdict: good.** The alternative, cascade deletion, quietly destroys work,
and this design refuses to do that anywhere.

### 20. The tree gets six levels deep

**What happens.** Nothing is refused. Traversals have a depth ceiling, and when
it is reached the counts say they are partial rather than pretending to be
complete. The guidance in [00](00-mental-model.md) is the only real defence.

**Verdict: a known weakness, accepted.** Enforcing a maximum depth would be
wrong for the occasional genuinely deep piece of work, and a partial count that
admits it is partial is better than a wrong count that does not.

---

## The three weaknesses worth remembering

Most of the cases above are handled cleanly. Three are not, and pretending
otherwise would make this document less useful.

```
   ① The system tracks identity, not meaning.
      A node rewritten in place still satisfies every link pointing at it.

   ② Coverage depends on habit.
      Everything derived comes from links people wrote. Where links are
      missing, the system is silent rather than wrong, which is the right
      failure direction, but it is still a gap.

   ③ Nothing prevents a badly shaped tree.
      Depth and breadth are guidance. The interface can nudge, and that is all.
```

Each of these was a deliberate choice to accept a visible imperfection instead
of building machinery that would guess. The next file,
[15 — Migration](15-migration-from-today.md), covers how the current system
grows into this one.
