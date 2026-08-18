# 06 — Conflicts

Three collisions exist in this project. One is settled by deciding the order,
one is accepted with a reason, and one is only a quiet note. Each shows a
different level of the mode matrix doing its job.

---

## Collision 1 — Two tasks rewriting `createComment()`

```
   function  app.services.createComment          ◌ planned, not written yet
        ▲                              ▲
        │ modify                       │ modify
        │                              │
   VN-22  Detect banned words     VN-30  Rate limiting
   ▸ Comments ▸ Moderation        ▸ root
   ○ to do                        ○ to do
```

VN-22 wants to call the word checker before saving. VN-30 wants to count how
many comments an account made this minute. Both changes are needed, and both
rewrite the same function.

Neither person knows about the other. VN-22 lives three levels down inside the
comments tree, VN-30 is a root task somebody filed on a different day.

### When it is noticed

The moment the second link is written. Neither function exists yet, so this is
found while both tasks are still text.

```
   ┌────────────────────────────────────────────────────────┐
   │ VN-22  Detect banned words                  ○ to do    │
   │ ⚑ contested — createComment() also modified by VN-30   │
   └────────────────────────────────────────────────────────┘

   canvas:  ◌ ƒ createComment()   ⚑2
   sidebar: CONTESTED  ⚑ createComment()  2
```

### How it is settled

Both changes are wanted, so there is nothing to remove. They simply must not
happen at once. The resolution is to decide the order.

```
   ┌──────────────────────────────────────────────────────────────┐
   │  createComment() — 2 tasks intend to modify it                │
   │                                                               │
   │  VN-30  Rate limiting            ○ to do                      │
   │  VN-22  Detect banned words      ○ to do                      │
   │                                                               │
   │  ● decide the order    ○ accept    ○ resolve    ○ delegate    │
   │                                                               │
   │    first:  ● VN-30    ○ VN-22                                 │
   │    reason: "rate limiting is a thin wrapper. moderation edits  │
   │             the body of the function, so it goes second."      │
   └──────────────────────────────────────────────────────────────┘
```

What gets written:

```
   VN-22 ──depends_on──► VN-30
   conflict decision: ordered, with the reason above, by Yared
```

What changes on screen:

```
   VN-22   ⛔ blocked — waiting for VN-30 (rate limiting)
   node    ⏭ sequenced, 2 tasks
   sidebar the row moves into the quieter sequenced section
   VN-11   🔴 1 blocked inside
   VN-3    🔴 count goes up by one
```

The agreement is now a real dependency, so nobody has to remember it. When
VN-30 moves to done, VN-22 becomes ready everywhere at once.

The decision record is what a bare dependency edge could never carry. Six months
later, somebody wondering why moderation waited for rate limiting can read one
sentence instead of guessing.

### One thing to notice about ordering

VN-22 already depended on VN-9, because VN-9 creates the function in the first
place. Adding the ordering edge produces a chain that is exactly right:

```
   VN-9  creates createComment()
     └─► VN-30  wraps it with rate limiting
           └─► VN-22  edits its body to call the word checker
```

Three tasks, one function, and a sequence nobody had to design. Each edge came
from a different source: two from link analysis, one from a human decision
about a collision.

---

## Collision 2 — Two tasks changing `renderPost()`

```
   function  app.web.renderPost                  ● exists
        ▲                              ▲
        │ modify                       │ modify
        │                              │
   VN-17  Show the author         VN-12  Show comments on the page
   ▸ Posts belong to users        ▸ Add comments
   ○ to do                        ○ to do
```

Both add something to the post page. One adds a line showing who wrote the
post, the other adds the comment list underneath it.

### Why this one is different

There is no reason to wait. Two different parts of one template, no shared
logic, and both changes are small. Ordering them would block one person for no
benefit.

```
   ┌──────────────────────────────────────────────────────────────┐
   │  renderPost() — 2 tasks intend to modify it                   │
   │                                                               │
   │  ○ decide the order   ● accept   ○ resolve   ○ delegate       │
   │                                                               │
   │    reason: "different parts of the same template. The author  │
   │             line is in the header, comments go at the bottom. │
   │             Whoever is second rebases in a minute."           │
   └──────────────────────────────────────────────────────────────┘
```

What gets written: one conflict decision. No dependency, no status change,
nothing else. The amber marker goes quiet on both cards and the node.

### When the decision stops applying

If either side later widens its links, the decision no longer describes the
situation, and the warning comes back with a note saying the earlier decision
was made about a narrower version of the work.

```
   ⚑ contested — renderPost()
     an earlier decision accepted this on 14 Aug, when VN-12 only added a
     comment list. VN-12 now also modifies the page header.
```

The record of the conversation survives. It just stops silencing something it
no longer covers.

---

## Collision 3 — Reading a class somebody is rewriting

```
   class  app.models.Post                        ● exists

   VN-16  Add an author_id field      ~ modify
   VN-9   Comment write path          ◦ read
   VN-8   Comment model               ◦ read
   VN-3   Add comments                ◦ read
```

One task is changing the class. Three tasks are reading it. This is the most
common shape in any codebase, and treating it as a conflict would put an amber
chip on almost everything.

```
   ┌────────────────────────────────────────────────────────────┐
   │ VN-9   Comment write path                       ○ to do    │
   │ ◦ class Post — being modified by VN-16                     │
   └────────────────────────────────────────────────────────────┘
```

Grey, small, at the bottom of the links list. Nobody is blocked and nothing
needs deciding. What it says is worth saying once: the plan for VN-9 was written
against a version of `Post` that is about to change, so it is worth a glance
before starting.

---

## What the contested list looks like

```
   ┌──────────────────────────────────────────┐
   │ CONTESTED                                 │
   │ ⚑ renderPost()             2   accepted   │
   │ ⏭ createComment()          2   sequenced  │
   │ ◦ class Post               1 writer, 3 readers │
   └──────────────────────────────────────────┘
```

Nothing is hidden. A situation that was handled is shown as handled rather than
removed, so somebody arriving later can tell the difference between "nobody
noticed" and "we talked about it".

---

## The collision that did not happen

Worth including, because it is the strongest thing this design does.

Suppose somebody in another part of the project files a task called "Comment
storage" and records:

```
   VN-44  Comment storage
     + class  app.models.Comment
```

VN-8 already plans to create exactly that class.

```
   ┌────────────────────────────────────────────────────────────┐
   │ ⚑ DUPLICATE                                                 │
   │   Two tasks plan to create class app.models.Comment:        │
   │     VN-8   Comment model      ▸ Add comments                │
   │     VN-44  Comment storage    ▸ root                        │
   │   Neither has been written yet.                             │
   └────────────────────────────────────────────────────────────┘
```

Two people planned the same class, probably in different weeks, without knowing
about each other. No code exists. In most tools this is found in code review,
or never.

It is found here because a `create` link is indexed by the name of a node that
does not exist yet, which is the same mechanism that makes the canvas draw
ghosts.

---

## A note on drafts

While VN-3's v2 was a draft, it declared `modify class Post`. That never
collided with VN-16, which is also modifying `class Post`, because drafts do
not take part in conflict detection.

The moment v2 was activated in [04](04-alternative-versions.md), the collision
appeared. That is the correct behaviour: writing down an idea should never
argue with somebody else's plan, and choosing it should.

Next: [07 — Lookups](07-lookups.md).
