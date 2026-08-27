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

**What happens.** The task is created almost empty: no document, no links, no
children, `parent_id` null unless somebody placed it. It sits on the board, it
can be moved between columns, it can be finished.

**Verdict: good.** There is no such thing as an unplanned task in the model,
which removes a whole category of special cases. A task with nothing written
down is simply a task with an empty document, and it behaves like every other
task. Small work stays small.

---

## 2. A task tries to depend on its own ancestor

VN-11 "Comment moderation" is a child of VN-3 "Add comments". Somebody writes
a dependency saying VN-3 depends on VN-11.

**What happens.** The system refuses with a sentence explaining the issue and
the solution:

```
   VN-3 cannot depend on VN-11, because VN-11 is a child of VN-3.
   Containment already says VN-3 waits for VN-11.
   
   If VN-11 must wait for something, add a dependency on that thing instead.
```

**Verdict: good.** The guard prevents a deadlock. The sentence teaches the
right model.

---

## 3. A task depends on its own descendant

VN-3 is a parent of VN-11, and VN-11 is a parent of VN-20. Somebody writes a
dependency saying VN-3 depends on VN-20.

**What happens.** The system drops the edge silently and writes an event:

```
{ type: "dependency_removed",
  payload: { reason: "redundant: target is a descendant" },
  at: ..., author: ... }
```

Containment already expresses this relationship (VN-3 waits for everything
under it). The edge is noise.

**Verdict: good.** The system does not block the user, but it does clean up
redundant edges automatically.

---

## 4. Cascade delete removes a subtree

A parent VN-3 "Add comments" is deleted. It has children VN-8, VN-9, VN-11,
and VN-11 has its own children VN-20, VN-21.

**What happens.** Soft delete: all seven tasks (VN-3, VN-8, VN-9, VN-11,
VN-20, VN-21, and any descendants of those) get `deleted_at` set to now, all
with the same `deleted_batch_id`.

Before confirming, the system warns about dependencies:

```
Deleting VN-3 removes 7 tasks.
2 tasks outside this subtree depend on tasks inside it:
   VN-14  ──depends_on──►  VN-11
   VN-16  ──depends_on──►  VN-8
These tasks will no longer be blocked.
```

The user can:
- Confirm the delete (inbound edges are removed)
- Cancel and reconsider

To undo, a single restore by `deleted_batch_id` brings back the whole subtree.

**Verdict: good.** Atomic soft delete with undo is far safer than orphaning
work.

---

## 5. A child affects a node that another task is affecting

**What happens.** Both tasks link the node with a write mode, so the pair is
contested. Both cards show it, the node shows it, and two resolutions are
offered, one of which creates a real dependency.

**Verdict: good.** This is the feature, not an edge case.

---

## 6. Two tasks affect the same node, and both are already in progress

**What happens.** Same as above, except neither can simply wait. The likely
resolution is `accepted` with a reason, or somebody narrows a scope so the links
stop overlapping and the conflict disappears on its own.

**Verdict: acceptable.** The system reports the situation accurately and
records the decision. It cannot merge anybody's code, and it does not pretend
to. Its contribution is that both people know on the day rather than at merge
time.

---

## 7. Two tasks each add a different method to the same class

The case that would have made conflict detection useless.

**What happens.** Each task links the *function it creates*, not the class.

```
   VN-8   create function Comment.validate    container: class Comment
   VN-44  create function Comment.render      container: class Comment

   derived:  class Comment is touched by both
   computed: no conflict — the typed links are on different nodes
```

Both still appear when somebody asks what touches `class Comment`, because
containment is derived. Neither triggers a warning, because neither claimed the
class itself changes.

**Verdict: good, and load-bearing.** Without the rule in
[05](05-graph-links.md) §3 both tasks would type "affects class Comment" and be
reported as colliding. Since almost all work adds or changes methods, nearly
every class in the codebase would sit permanently amber, and a warning that is
usually wrong is a warning people train themselves to click past. Getting this
wrong would not degrade conflict detection — it would destroy it.

The distinction is real, not a technicality: *changing the class* and *changing
something inside the class* are different claims, and only the first one means
two people are about to edit the same lines.

---

## 8. A task in the backlog links a node somebody is actively rewriting

**What happens.** The pair produces a **watch**, not a conflict, because
severity reads task status: one side is a claim, the other is still an idea.

```
   VN-30  Rate limiting     ● in progress    affects createComment()
   VN-52  Retry policy      ○ backlog        affects createComment()

   ⚑ watch — quiet note on VN-52, nothing loud on VN-30
```

**Verdict: good, with one honest gap.** Somebody working out of the backlog
without moving the card gets no warning, and nobody gets warned about them. The
answer is a housekeeping list — *draft tasks with links, unchanged for N days* —
rather than a `provisional` flag on the link. A stale list can be ignored
harmlessly; a stale flag silently changes what the system reports.

---

## 9. A task is blocked by another task

**What happens.** One stored edge, computed blocking, chips on both sides with
breadcrumbs, and rollup to the parent so nothing hides in the tree.

**Verdict: good.**

---

## 10. A task deep in one tree is blocked by a task deep in another tree

VN-9, three levels inside Comments, needs VN-5, two levels inside
Authentication.

**What happens.** The edge is allowed, because dependencies connect tasks at
any depth. Both chips carry breadcrumbs so the other side can be found. Both
parents show a rollup marker.

**Verdict: good.** This is exactly the precision the recursive model buys, and
it is the case a task-level-only dependency system handles badly, since it
would force "Comments depends on Authentication" and stop four unrelated tasks.

---

## 11. A graph node is deleted, and a link still points at it

**What happens.** The link keeps its name snapshot and becomes `unresolved`. It
displays as a warning that still reads sensibly, with three actions: point at
another node, remove the link, or change it into a `delete` link, which may be
exactly what the work was.

**Verdict: good.** This is why every link is a soft reference carrying a name
snapshot rather than a hard database link that the parser would break on its
next pass.

---

## 12. A node still exists but has changed completely

The function is still called `createComment`, but it was rewritten and now does
something else entirely.

**What happens.** The link still resolves, because the node id is the same, and
the system has no way to know the meaning changed from structure alone.

**Verdict: a real weakness, with one partial defence and one optional cure.**
The system tracks identity, not meaning. The partial defence is that a rewrite
is itself somebody's work, and if that work recorded a `affects` link on the
node, then anybody else linking it sees a contested or watch marker.

The optional cure is `verified_by_tests` (see [05](05-graph-links.md) §6). A
task that names the test nodes which must pass is verified by behaviour rather
than by structure, and a rewrite that breaks meaning breaks the tests. Where
neither a task nor a test covers the rewrite, the planning layer cannot know.
This is the honest limit of planning on top of structure.

---

## 13. A task is split into several tasks

**What happens.** The split operation creates the new tasks as children of the
original, moves selected links down to them, and writes a `task_created` event
on each. The original task keeps its identity, its key, its dependencies, and
its own `parent_id`.

**Verdict: good**, and notably better than a flat model, where splitting either
loses the original or creates a fake parent. Here the original simply gains
children, which is a thing every task can do.

---

## 14. A task is duplicated by mistake

Two people file "Add comment moderation" a week apart.

**What happens.** If both wrote links, the system spots it before either starts:
two tasks planning to create the same `(qname, kind)` produce a duplicate
warning, which is the strongest early signal in the design.

If neither wrote links, nothing is detected automatically, and somebody notices
by reading. Merging is manual: reparent the duplicate's children under the
survivor by setting their `parent_id`, copy anything useful out of its document,
then delete the duplicate with an event saying where it went.

**Verdict: good when links exist, acceptable when they do not.** There is no
`duplicates` relationship, because marking a duplicate is housekeeping rather
than a fact worth modelling.

---

## 15. A plan creates a node that does not exist yet

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

## 16. One node is affected by many tasks

A popular class is linked by fifteen tasks.

**What happens.** The node summary lists them grouped by mode, so the important
distinction is immediate: three intend to change it, twelve only read it. The
badge shows the write count, not the total, because fifteen is noise and three
is a decision.

**Verdict: good.** Grouping by mode is what stops popular nodes from being
permanently amber.

---

## 17. One task affects many nodes

A big refactor touches sixty nodes.

**What happens.** The links are listed, grouped by kind and mode, and collapsed
by default with counts. Rollup means the parent card can say "affects 60
nodes" without listing them.

**Verdict: acceptable, with a nudge.** Sixty affected nodes on one leaf task
usually means the task should have children. The interface can say so as a hint,
but it must not refuse, because some refactors genuinely are one sweep.

---

## Five more the single-parent tree invites

### 18. Somebody tries to give a task a second parent

Two people both want "Show comments on the post page" under their own epic.

**What happens.** Impossible by construction. `parent_id` is a scalar, so
setting a new parent moves the task rather than adding one. Whoever moves it
second wins, and the first parent sees it leave.

The honest answer to genuinely shared work is a dependency. The task lives under
one parent, and the other side depends on it:

```
   VN-12 "Show comments on the post page"
     parent_id = VN-3   Add comments

   VN-40 "Post page redesign"
     depends_on ──► VN-12
```

Both parents see the relationship — VN-3 as containment, VN-40 as a dependency
in its "depends on" list, and VN-12 shows both in its detail panel.

**Verdict: good.** This is the case multi-parent existed to serve, and the
dependency says something truer: VN-40 is not responsible for VN-12, it is
waiting on it.

### 19. Somebody tries to make a cycle

Either by reparenting a task under its own descendant, or by adding a dependency
that loops.

**What happens.** Both are refused with the path that would have formed. The
containment check walks up `parent_id` (a linked list, bounded by a depth
ceiling), and the dependency check walks `depends_on`. They are separate checks
on separate edges.

```
   Refused: VN-3 cannot be moved under VN-11, because VN-11 is inside VN-3.
   Refused: VN-9 → VN-30 → VN-44 → VN-9
```

**Verdict: good, and cheaper than before.** With a single parent, ancestry is a
walk up a chain rather than a traversal of a graph.

### 20. A parent is deleted while its children are still wanted

**What happens.** The whole subtree is deleted — this is a cascade, and it is
deliberate. Every task in the subtree gets `deleted_at` set and a shared
`deleted_batch_id`.

Two things keep this from destroying work. The delete is **soft**, so one undo
restores the entire subtree. And before confirming, the system names every
dependency crossing the boundary:

```
   Deleting VN-3 removes 7 tasks.
   2 tasks outside this subtree depend on tasks inside it:
      VN-9  ──depends_on──►  VN-5
      VN-14 ──depends_on──►  VN-6
   These tasks will no longer be blocked.
```

**Verdict: good, and better than the orphan rescue it replaces.** Orphaning
children left them alive but unreachable from any plan, which read as
housekeeping debt nobody ever cleared. A reversible cascade with a named blast
radius is a decision somebody makes on purpose.

The one thing to get right in the interface: if a child genuinely should
survive, the answer is to reparent it out of the subtree **before** deleting,
and the warning dialog should offer exactly that.

### 21. Somebody restores a subtree into a hole

VN-3 was deleted with its children. Two weeks later somebody restores it, but
in the meantime VN-3's own parent was deleted too.

**What happens.** Restore by `deleted_batch_id` brings back exactly the tasks in
that batch. If the restored subtree's root has a `parent_id` pointing at a task
that is still deleted, the root is restored as **top-level** (`parent_id` set to
null) and an event records the change.

**Verdict: acceptable.** The alternative — refusing the restore, or resurrecting
the parent's batch as well — either blocks recovery or restores more than
somebody asked for. Landing at the root is visible and easy to correct.

### 22. The tree gets six levels deep

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
      Partly curable by verified_by_tests, which checks behaviour instead.

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
