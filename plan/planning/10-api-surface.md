# 10 — Operations

This file lists what the planning system has to be able to do, described as
operations rather than as endpoints. Each one says what it takes, what it
guarantees, and what it refuses.

Two rules run through all of them.

**Every write is safe to repeat.** Network calls fail and get retried, two
panels can trigger the same action, and an agent may repeat a step. So adding
something that is already there does nothing rather than creating a duplicate,
and removing something that is already gone does nothing rather than failing.

**Every refusal explains itself in a sentence a person can act on.** Not an
error code. A sentence naming what was wrong and what to do instead.

---

## 1. Reads

### Board level

Takes the task whose children should be shown, or nothing for the root level.

Returns the tasks at that level with everything computed: status, blocked,
waiting on code, ready, progress, rollup counts, contested markers, shared and
orphaned flags, and the breadcrumb path to the current level.

The root level returns every task that no active version refers to. That
includes brand new tasks nobody has placed yet and orphans left behind by a
version change, which is exactly right, because both are things somebody needs
to look at.

### Task detail

Takes one task. Returns everything about it: its fields, its active version
with the document, the context and affects lists with each link's computed
state, its children with their conditions, its dependencies in both directions
with breadcrumbs, its conflicts, its other versions in summary form, and its
notes.

This is the only read that returns a full document, which keeps the board
payload small.

### Node work summary

Takes a set of node ids. Returns, for each one, the tasks that link to it with
their modes, whether it is contested, whether a conflict has been sequenced by
a dependency, and whether anything plans to create a node with that name.

One call serves the canvas badges, the node popover, the sidebar tree badges,
and the contested list. Nothing recomputes this for itself.

### Version comparison

Takes a task and two of its versions. Returns the four things a version owns,
side by side: summary, document, links grouped by mode, and children with a
marker on the ones that appear in both.

### Suggestions

Three read-only helpers that never change anything:

| Suggestion | Based on |
|---|---|
| Dependencies this task probably needs | its links that need nodes other tasks plan to create |
| Nodes this task probably touches | the callers and callees of nodes it already links |
| Replacements for a broken link | name and kind similarity against live nodes |

Each returns candidates with a reason attached, and a person decides. Nothing
is applied automatically.

---

## 2. Task writes

### Create a task

Takes a title, and optionally a parent to attach it to, a position in that
parent's list, a first anchor, and a description.

Guarantees: a key is minted, a first version is created and made active, and if
a parent was given, the reference is added to that parent's active version. A
task created without a parent is a root task, which is normal and not an error.

### Update a task's fields

Title, description, type, priority, labels. Ordinary, and no rules attached.

### Move a task to another column

Takes a status and a position. Writes a note. If the task has children that are
not finished and the target column means done, it asks what should happen to the
children rather than deciding, as described in
[04](04-lifecycle-and-status.md).

### Move a task to a different parent

Takes the new parent and a position, and optionally the old parent to remove it
from. Because a task can have several parents, adding and removing are separate
things, and moving is simply both at once.

Refuses if the move would put a task inside itself, naming the cycle.

### Delete a task

Removes it, removes every reference to it from every version that names it, and
removes every dependency pointing at it, writing a note on each affected task.

Children are **not** deleted. They may have other parents, and even when they do
not, silently deleting work because its parent was deleted is the one thing this
design refuses to do. Children with no remaining parent become root tasks, where
they are visible.

Refuses to delete a task that has children unless the caller confirms, and says
how many children will become root tasks.

---

## 3. Children

### Add a child reference

Takes a version, a task, and a position. Adding a task that is already in the
list moves it to the new position rather than duplicating it.

Refuses if the child is an ancestor of the parent, naming the cycle.

### Remove a child reference

Removes the pointer. The task itself is untouched and becomes orphaned if no
other active version refers to it, which is a state rather than a problem.

### Reorder children

Takes the version and the new order. Order is reading advice and never blocks
anything, so this operation has no consequences beyond display and the order an
agent reads.

### Promote and split

Two conveniences built from the operations above, offered because they are the
two things people do most while planning:

**Promote** takes a child and moves it up to be a sibling of its parent. It is
a remove and an add.

**Split** takes a task and a list of titles, creates those tasks as its
children, and optionally moves some of the parent's links down to them. It is a
create and a set of adds, with a note recording the split.

---

## 4. Links and anchors

### Add a link

Takes a version, a node, and a mode. The node is given either by id, for
something that exists, or by name and kind, for something that does not exist
yet.

Adding a link that is already there with the same mode does nothing. Adding one
that exists with a different mode changes the mode and writes a note, since
that is what the caller meant.

Refuses `create` on a node id that already exists, saying that the node is
already there and asking whether `modify` was meant. Refuses `create`, `modify`
and `delete` on call nodes, and offers the containing function instead.

### Remove a link

Keyed by the node, never by a position in a list. A position shifts when
somebody else edits the same version, and a retry after a timeout would then
remove the wrong thing.

### Move a link

One operation that changes which node a link points at, keeping its mode and
note. This is what repairs a link after a rename, and it is the same operation
whether the old node still exists or not.

### Anchors

Add, remove, and move, all keyed by node id, all idempotent, exactly as they
work today. Anchors sit on the task rather than on a version and are unchanged
by activation.

---

## 5. Dependencies

### Add a dependency

Takes two tasks. Refuses in three cases, each with its own sentence:

```
   the two are the same task
   one is an ancestor or descendant of the other
        "VN-11 is part of VN-3, so it cannot depend on it. If it is waiting
         for something specific inside VN-3, point at that task instead."
   the edge would create a cycle
        naming the path that would have formed
```

### Remove a dependency

Idempotent. Writes a note on both sides.

---

## 6. Conflicts

### Read conflicts

For a node, for a task, or for the whole project. Computed on every call, never
stored.

### Record a decision

Takes the node, the tasks involved, and one of the four decisions.

`ordered` also creates the dependency, in one operation, so the agreement and
its consequence cannot get out of step. If that dependency would be refused for
any of the reasons above, the whole decision is refused and the reason is shown.

`accepted`, `resolved`, and `delegated` record the decision without changing any
work.

### Retire a decision

Marks a decision as no longer applying. Also happens automatically when the
links it was about have changed enough that the decision no longer describes
anything, in which case the record is kept and shown as historical.

---

## 7. What every write does besides its own job

```
   1. Writes a note when the change is worth remembering, and only then.
      Toggling something on and off leaves no trace, so the history never
      fills up with noise.

   2. Clears the summaries the change could affect.

   3. Emits an event so other open surfaces refetch.
```

The third one is what makes the canvas badge update when somebody changes a
plan in another panel, and it uses the socket layer that already exists.

---

## 8. Operations deliberately left out

| Not built | Why |
|---|---|
| Bulk import of tasks | Nothing needs it yet, and it invites badly shaped trees created in one go |
| Templates | A fork of an existing version covers most of what a template would do |
| Assignment and notifications | Postponed, listed in [16](16-open-questions.md) |
| Automatic dependency creation | Suggestions only. An invented dependency misleads everybody who reads the board |
| Automatic link repair after a rename | Suggestions only, for the same reason |
| Archiving | Deleting and orphaning cover the real cases, and an archive is a third state that needs its own rules everywhere |

The next file, [11 — UI surfaces](11-ui-surfaces.md), shows where each of these
operations is triggered from.
