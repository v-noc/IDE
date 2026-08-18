# 07 — Versions and Alternatives

Most of the time a task has one version and nobody ever thinks about versions
at all. This file is about the times when that is not enough: when there are
two sensible ways to do something, when an approach has to be rewritten
halfway through, and when somebody needs to know six months later what was
considered and rejected.

---

## 1. One mechanism, two uses

Two different situations come up, and they feel different when you are living
through them.

```
   ALTERNATIVES                          REVISIONS
   ────────────                          ─────────
   Nothing has been chosen yet.          Something was chosen, work started,
   Two or three ways to do this are      and reality disagreed. The approach
   written down side by side so they     needs to change while the task is
   can be compared.                      already in progress.

   "Separate Comment class"              "v1 said the service layer validates.
   "Comments stored inside Post"          After writing it, validation clearly
                                          belongs in the repository. v2."
```

They are the same object. What tells them apart is a single field,
`derived_from`.

```
   version 1  "Separate Comment class"        derived_from: —      a fresh idea
   version 2  "Comments stored inside Post"   derived_from: —      a fresh idea
   version 3  "Separate class, repository     derived_from: v1     a revision
              owns validation"
```

A version with no `derived_from` is an independent idea. A version that has one
started as a copy of another and was then changed. That single field is enough
for the interface to show a revision as a continuation, with a comparison
against its parent, and to show alternatives as siblings.

Building two mechanisms for this would mean two sets of rules, two screens, and
a constant question about which one to use. One mechanism with one field costs
almost nothing and covers both.

---

## 2. Creating a version

There are two ways to make one, and they map exactly onto the two situations
above.

**Start fresh.** An empty version with its own name, its own document, its own
links, and no children. Used when the new idea is genuinely different.

**Fork an existing version.** A copy of the document, the links, and the child
list. Used when most of the approach survives and a part of it changes.

```
   FORK v1 ──► v3

   v3 starts as an exact copy of v1:
     same document text, which you then edit
     same links
     same child references, pointing at THE SAME child tasks

   ⚠ the children are referenced, not copied.
     VN-8 is now referred to by v1 and by v3. It is one task.
     If it is done, it is done in both.
```

That last point is the one that surprises people and is also the one that makes
everything work. Forking a version does not duplicate work. It duplicates the
description of the work.

---

## 3. Activation

Only one version of a task is active at a time. Activating is a small
operation, and this is the entire list of what it changes:

```
   1. The task's active_version_id points at the new version.
   2. The previous active version becomes superseded, with a timestamp.
   3. A note is written on the task.
```

Everything else people expect to happen is computed afterwards rather than
performed:

```
   AFTER ACTIVATING v2 OF "Add comments"

   the board level for VN-3 now lists v2's children
   children referenced only by v1        ⇒ shown as orphaned, not deleted
   children referenced by both           ⇒ untouched, status preserved
   v1's node links                       ⇒ stop counting for conflicts
   v2's node links                       ⇒ start counting for conflicts
   dependencies on VN-3                  ⇒ unchanged, they point at the task
```

Nothing is destroyed, and nothing needs rescuing. This is the property the whole
model is built around, and it is worth seeing in a picture.

```
   BEFORE                                AFTER activating v2
   ──────                                ───────────────────
   VN-3 ── v1 ★                          VN-3 ── v1  superseded
            ├─► VN-8   done                       ├─► VN-8   done   ⌫ orphaned
            ├─► VN-9   doing                      ├─► VN-9   doing  ⌫ orphaned
            └─► VN-12  todo                       └─► VN-12  todo
        ── v2  draft                          ── v2 ★ active
            ├─► VN-15  todo                       ├─► VN-15  todo
            └─► VN-12  todo                       └─► VN-12  todo
                                                        ▲
   VN-12 appears in both, so it is not orphaned ────────┘
   and it keeps whatever status it had.
```

---

## 4. What happens to work that was already finished

This is the question that breaks most planning tools, and here it has a boring
answer, which is the best kind.

```
   VN-8  "Comment model"   was finished under v1.
   v2 does not refer to it.

   What happens to VN-8?
     nothing.
     It is still a task. It is still done. Its history is intact.
     It is marked as not part of any active plan.
```

The work exists in the repository. The task recording it exists on the board.
Neither of them depends on somebody's current description of the approach.

Three things can be done with it, and all three are honest choices:

| Choice | When it is right |
|---|---|
| Leave it orphaned | The work is done, it is not part of the current approach, and the record should show that |
| Add it to the new version | It turns out the new approach needs it too. One click, and it is no longer orphaned |
| Delete it | It was a mistake, and the code was reverted |

The interface never picks for you, because all three are real and the system
cannot tell which one applies.

### The reverse case: partly finished work under a replaced approach

```
   VN-9  "Comment write path"   was in progress under v1, half written.
   v2 takes a different route and does not need it.
```

The same answer applies, with one addition. Because VN-9 has `create` links,
the system can say something useful about what is left behind:

```
   ⌫ VN-9 is not part of any active plan
     it created:  function app.services.createComment   ← still in the codebase
     nothing in any active plan mentions this function
```

That is a genuinely valuable sentence. It is how abandoned code gets noticed,
and no ordinary task board can produce it.

---

## 5. Comparing versions

When a task has more than one version, the detail panel offers a side by side
comparison. It compares the four things a version owns.

```
                  v1  Separate Comment class      v2  Comments inside Post
   ─────────────────────────────────────────────────────────────────────────
   summary        A Comment class with its        Posts hold a list of
                  own storage, linked to Post     comments in the document
                  and User.                       itself.

   creates        class    Comment                —
                  function createComment()
                  function listComments()

   modifies       function renderPost             class    Post
                                                  function renderPost

   deletes        —                               —

   reads          class Post · class User         class Post · class User

   children       5   (VN-8, VN-9, VN-10,          2   (VN-15, VN-12)
                       VN-11, VN-12)

   shared         VN-12 appears in both
   ─────────────────────────────────────────────────────────────────────────
```

The valuable rows are the link rows, because they show the real consequences of
the choice. One approach adds a class and two functions; the other changes an
existing class that other work is already reading. That second fact is exactly
the kind of thing that decides an argument, and it comes for free from data
people already entered.

**Tradeoff.** The comparison only shows what was written down. A version whose
author did not bother with links looks cheap next to one whose author was
thorough. The interface reduces this by showing counts of what is missing, such
as "no links recorded", rather than presenting an empty list as if it meant no
impact.

---

## 6. Versions can exist at any depth

A task three levels down can have two versions, because it is a task like any
other.

```
   VN-3   Add comments                        1 version
     └── VN-11  Comment moderation            2 versions   ← the decision lives here
            ├── v1  "Keyword filter"     ★
            └── v2  "Manual review queue"
```

This is usually the right place for the decision, because that is where the
real choice is. The parent does not need alternatives just because a child has
them.

The cost is that somebody looking at the tree needs to see where the branching
is. The interface handles it with a small marker on the card and by carrying
the version name in the breadcrumb when you are inside that task's level:

```
   ▸ Comments ▸ Moderation (v1 Keyword filter) ▸
```

**When both a parent and a child have versions**, the combination could get
confusing in theory. In practice it is fine, because a version only ever
controls its own children. The parent's active version decides whether the
child is in the plan at all, and the child's active version decides how the
child is done. Those are separate questions and the breadcrumb answers both.

---

## 7. When not to create a version

Versions are for real alternatives, not for edits. Most changes to a plan are
just edits.

```
   JUST EDIT THE ACTIVE VERSION          MAKE A NEW VERSION
   ────────────────────────────          ──────────────────
   adding a step you forgot              a genuinely different approach
   fixing a wrong link                   an approach you want to compare
   rewording the document                a rewrite big enough that somebody
   reordering the children                would want to read the old one
   splitting one child into two          a change of direction after work
                                          has already started
```

The test is whether anybody would ever want to read the old version. If not,
edit in place. Creating a version for every edit turns a useful record into a
noisy one, and people stop reading it.

**Tradeoff.** Editing in place means the fine grained history of a plan is not
in the planning model. That is deliberate. Fine grained history already exists
in commits, since the task documents live in the same versioned database as
everything else, and duplicating it inside the planning model would double the
storage and the confusion for very little gain.

---

## 8. Costs of having versions at all

**One more layer of indirection.** The document, the links, and the children
live on a version rather than directly on the task. Every read passes through
the active version pointer. This is hidden while a task has one version, which
is the normal case, but it is real complexity in the model and in every query.

**A second place where "which one am I looking at?" can go wrong.** The
interface has to be disciplined about showing the active version's name
wherever a version's content is displayed.

**Comparison invites over-planning.** Because writing an alternative is easy,
somebody can spend a day writing three versions of a task that needed twenty
minutes of work. Nothing in the model prevents that; the guidance in
[00](00-mental-model.md) about depth applies equally to breadth.

Against those costs: the ability to write down two approaches, choose one, keep
the other, change your mind later, and never lose work. Every one of those is
something people already do informally, in documents nobody can find, and this
puts them where the work is.

The next file, [08 — Conflicts and concurrency](08-conflicts-and-concurrency.md),
covers what happens when two pieces of work want the same node at the same
time.
