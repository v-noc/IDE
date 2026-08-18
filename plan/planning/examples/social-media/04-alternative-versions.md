# 04 — Alternative Versions

The comments document mentioned a rejected idea: storing comments inside the
post instead of as their own class. That idea is written down as a real second
version, and this file follows what happens when somebody takes it seriously,
activates it, and then changes their mind again.

---

## The second version

```
   TASK  VN-3   Add comments
   ⑂ v1  Separate Comment class ★active   |   v2  Comments inside Post
   ────────────────────────────────────────────────────────────────────────
   v2  Comments inside Post              state: draft
       derived_from: —                   a fresh idea, not a revision of v1

   summary   A post carries its comments with it. No new class, no join, and
             one read to render a page.

   document  ## Approach
             Post gains a comments list. Writing a comment appends to it.
             Rendering the page needs no extra query at all.
             ## Cost
             Posts grow without limit. Moderating one comment rewrites the
             whole post. Listing recent comments across all posts becomes a
             scan of every post.
             ## When this would be right
             If comments were rare and always read together with the post.
             They are not going to be.

   affects   ~ class     app.models.Post
             note: "comments list holding author, body, and created_at"
             ~ function  app.web.renderPost

   children  1  VN-15  Add a comments list to Post
             2  VN-12  Show comments on the post page   ← the same task as v1
```

Two details carry most of the value.

**VN-12 appears in both versions.** Showing comments on the page is needed
either way, so both versions point at the same task. It is one task, with one
status and one history, referenced twice.

**v2 is a draft, so it affects nothing.** Its links do not take part in
conflict detection, its children do not appear on the board level, and its
pending creates are not expected by anybody. Two competing approaches written
by the same person never fight with each other on screen.

---

## Comparing them

```
                     v1  Separate Comment class      v2  Comments inside Post
   ──────────────────────────────────────────────────────────────────────────
   creates           class    Comment                 —
                     function createComment()
                     function listComments()

   modifies          class    Comment                 class    Post   ⚑
                     function renderPost()            function renderPost()

   reads             class Post · class User          class Post · class User

   children          5                                2
   shared children   VN-12 ──────────────────────────  VN-12

   pending creates   3                                 0
   ──────────────────────────────────────────────────────────────────────────
```

The link rows are what settle the argument, and they cost nothing because
somebody already entered them for other reasons.

The amber marker on v2's `class Post` row is the useful one. VN-16 in the other
tree is already modifying that class, and two tasks in this tree read it.
Choosing v2 means rewriting a class that three other pieces of work are already
involved with. Choosing v1 means adding a new class that nothing else touches
yet. That is a real difference in risk, and it appears without anybody
analysing anything.

---

## Activating v2

Suppose somebody decides v2 is worth trying. By this point VN-8 is finished.

```
   BEFORE
   VN-3 ── v1 ★active
            ├─► VN-8   Comment model             ✓ done · verified
            ├─► VN-9   Comment write path        ● in progress
            ├─► VN-10  Comment read path         ○ to do
            ├─► VN-11  Comment moderation        ○ to do
            └─► VN-12  Show comments             ○ to do
        ── v2  draft
            ├─► VN-15  Add a comments list       ○ to do
            └─► VN-12  Show comments             ○ to do
```

Activate v2. Three things are written:

```
   1. VN-3's active version pointer moves to v2
   2. v1 is marked superseded, with a timestamp
   3. a note on VN-3:
      "activated v2 (Comments inside Post), replacing v1 (Separate Comment class)"
```

Nothing else is performed. Everything below is computed on the next read.

```
   AFTER
   VN-3 ── v1  superseded
            ├─► VN-8   ✓ done · verified   ⌫ not in any active plan
            ├─► VN-9   ● in progress       ⌫ not in any active plan
            ├─► VN-10  ○ to do             ⌫ not in any active plan
            ├─► VN-11  ○ to do             ⌫ not in any active plan
            └─► VN-12  ○ to do             ← still in a plan, via v2
        ── v2 ★active
            ├─► VN-15  ○ to do
            └─► VN-12  ○ to do

   board level for VN-3 now shows 2 cards: VN-15 and VN-12
   VN-12 keeps its status, because it is the same task
   contested markers recompute: class Post is now contested by VN-16 and VN-3
```

### What the orphaned tasks say about themselves

```
   ⌫ VN-8   Comment model                     ✓ done
     not part of any active plan
     it created:  class app.models.Comment    ← still in the codebase
     nothing in any active plan mentions this class
```

That is the sentence an ordinary board could never produce. A class was built,
the approach that needed it was replaced, and the code is still sitting there.
Somebody has to decide whether to delete it, and now they know it exists.

```
   ⌫ VN-9   Comment write path                ● in progress
     not part of any active plan
     half written. Its pending create for createComment() is no longer
     expected by any active plan.
```

Also useful. Work in progress under a replaced approach is exactly the thing
that gets forgotten and half-merged.

---

## Changing your mind back

A week later, posts are growing and moderation is awkward. v1 was right.

```
   Activate v1 again.

   v2 becomes superseded.
   VN-8, VN-9, VN-10, VN-11 stop being orphaned. VN-8 is still done.
   VN-15 becomes orphaned.
   VN-12 is untouched, again, because it was in both.
   The board level for VN-3 shows 5 cards again.
```

Nothing was recovered, because nothing was lost. Switching approaches is a
pointer move in both directions, and the second switch costs exactly as little
as the first.

The only thing that carries a real cost is the code that was written under v2,
and the orphan chips are what make that cost visible instead of invisible.

---

## What this would have looked like without versions

Worth spelling out, because it is the case that shapes the model.

```
   If the children belonged to the approach itself, then replacing the
   approach would mean choosing between:

     delete them        VN-8 was finished. Deleting it destroys a real record
                        of work that is in the repository.

     keep them attached The board shows work belonging to an approach nobody
                        is following.

     move them across   The system invents an intention nobody expressed.

   Because a version only refers to children, none of those choices has to be
   made. The children are simply not referred to for a while.
```

Next: [05 — Dependencies and readiness](05-dependencies-and-readiness.md), with
v1 active again.
