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
waiting on code, ready, progress, rollup counts, contested markers, and the
breadcrumb path to the current level.

The root level returns every task `where parent_id is null`. Brand new tasks
nobody has placed yet and deliberate top-level goals are the same thing, which
is now correct rather than a conflation.

Every read filters `deleted_at is null` by default.

### Task detail

Takes one task. Returns everything about it: its fields, its document, the
context and affects lists with each link's computed state, its children with
their conditions, its dependencies **in both directions** with breadcrumbs, its
conflicts, and its events.

Both dependency directions matter more than they used to. With a single parent,
a genuinely shared step lives under one parent and the other side sees it only
as a dependency. Without a reverse list, that relationship is invisible from one
end.

This is the only read that returns a full document, which keeps the board
payload small.

### Node work summary

Takes a set of node ids. Returns, for each one, the tasks that link to it with
their modes, whether it is contested, whether a conflict has been sequenced by
a dependency, and whether anything plans to create a node with that name.

One call serves the canvas badges, the node popover, the sidebar tree badges,
and the contested list. Nothing recomputes this for itself.

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

Takes a title, and optionally a parent, a position among that parent's children,
a first link with its mode, and a description.

Guarantees: a key is minted, `parent_id` and `position` are set if a parent was
given, and a `task_created` event is written. A task created without a parent is
top-level, which is normal and not an error.

### Update a task's fields

Title, description, type, priority, labels, document. Ordinary, and no rules
attached.

### Move a task to another column

Takes a status and a rank. Writes a `status_changed` event. If the task has
children that are not finished and the target column means done, it asks what
should happen to the children rather than deciding, as described in
[04](04-lifecycle-and-status.md).

### Move a task to a different parent

Takes the new parent (or null for top-level) and a position. This is **one
write**: it sets `parent_id` and `position` on the task being moved. There is no
"remove from old parent" step, because the old parent never held a list.

Guarded on both sides, per [rules.md](rules.md) §6:

| Case | Verdict |
|---|---|
| new parent is a descendant of the task | refuse — containment cycle, name the path |
| the task depends on the new parent | refuse, name the dependency edge to remove |
| the new parent depends on the task | drop that dependency, write an event |

Writes a `parent_changed` event carrying the old and new parent.

### Delete a task

**Deletes the whole subtree.** Every descendant gets `deleted_at` set and a
shared `deleted_batch_id`, so one undo restores all of it.

Before deleting, the caller gets the blast radius: how many tasks will be
removed, and every dependency that crosses the boundary.

```
   Deleting VN-3 removes 7 tasks.
   2 tasks outside this subtree depend on tasks inside it:
      VN-9  ──depends_on──►  VN-5
      VN-14 ──depends_on──►  VN-6
   These tasks will no longer be blocked.
```

On confirm: soft-delete the subtree, remove those inbound `depends_on` edges,
and write an event on each affected outside task so nobody's card silently
turns ready.

If a child should survive, the answer is to reparent it out of the subtree
first. The confirmation offers exactly that.

### Restore a delete

Takes a `deleted_batch_id`. Clears `deleted_at` on every task in the batch and
writes a `restored` event.

If the restored subtree's root has a `parent_id` pointing at a task that is
still deleted, the root comes back as top-level and the event records it.

---

## 3. Children

Children are a query, not a stored list, so there are no add or remove
operations here. Attaching a child **is** setting its `parent_id`, which is the
reparent operation above.

### Reorder siblings

Takes a task and its new `position`. Lexorank means inserting between two
siblings is one write that touches no other row.

Order is reading advice and never blocks anything, so this operation has no
consequences beyond display and the order an agent reads.

### Promote and split

Two conveniences built from the operations above, offered because they are the
two things people do most while planning:

**Promote** takes a child and moves it up to be a sibling of its parent. It is
a remove and an add.

**Split** takes a task and a list of titles, creates those tasks as its
children, and optionally moves some of the parent's links down to them. It is a
create and a set of adds, with a note recording the split.

---

## 4. Links

There is one way a task points at code, so there is one set of link operations.

### Add a link

Takes a task, a node, and a mode. The node is given either by id, for
something that exists, or by **container plus leaf name plus kind**, for
something that does not exist yet. The qname is derived from those three, never
free-texted, because a typo leaves a link pending forever and that looks
identical to work never being done.

Adding a link that is already there with the same mode does nothing. Adding one
that exists with a different mode changes the mode and writes an event, since
that is what the caller meant.

Refuses `create` on a node id that already exists, saying that the node is
already there and asking whether `affects` was meant. Refuses `create`, `affects`
and `delete` on call nodes, and offers the containing function instead.

### Remove a link

Keyed by the node — by `node_id` when it resolves, by `(qname, kind)` when it
does not — never by a position in a list. A position shifts when somebody else
edits the same task, and a retry after a timeout would then remove the wrong
thing.

### Move a link

One operation that changes which node a link points at, keeping its mode and
note. This is what repairs a link after a rename, and it is the same operation
whether the old node still exists or not.

**All three are idempotent and keyed by the node, never by list index**, which
is what lets any of them be retried safely after a timeout.

There is no separate write for a container. A task that adds a method to a class
writes one `create` link on the function; the class's involvement is derived.
Writing `affects class Comment` is a different claim — the class itself changes
— and the API does not conflate them.

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

Idempotent. Writes a `dependency_added` event on both sides.

---

## 6. Conflicts

### Read conflicts

For a node, for a task, or for the whole project. Computed on every call, never
stored.

### Record a decision

Takes the node, the tasks involved, and one of the two decisions.

`ordered` also creates the dependency, in one operation, so the agreement and
its consequence cannot get out of step. If that dependency would be refused for
any of the reasons above, the whole decision is refused and the reason is shown.

`accepted` records the decision with its reason and changes no work. The warning
stays quiet unless the links change.

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
| Templates | Copying a task and its subtree covers most of what a template would do |
| Assignment and notifications | Postponed, listed in [16](16-open-questions.md) |
| Automatic dependency creation | Suggestions only. An invented dependency misleads everybody who reads the board |
| Automatic link repair after a rename | Suggestions only, for the same reason |
| Archiving | Soft delete already keeps the record and supports undo; an archive would be a third state needing its own rules everywhere |

The next file, [11 — UI surfaces](11-ui-surfaces.md), shows where each of these
operations is triggered from.
