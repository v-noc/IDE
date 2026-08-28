# 13 — Flows

Ten walkthroughs of ordinary situations. Each one shows what a person does,
what the system does in response, and what changes on screen. They are written
in order of how often they happen.

Throughout, the project is the small social media application: `User` and
`Post` already exist, and comments are being added.

---

## Flow 1 — Create a task from the canvas

The most common way work starts, and the one that produces the best data.

```
   1. Right-click the file  app/services/comment_service.py  on the canvas
      → "New task here"

   2. The dialog opens with the node already filled in:
         file  comment_service.py

   3. One question is asked about the node:
         "Will this work read it, change it, or remove it?"
         ○ read    ● change    ○ remove

   4. Title and description are typed. Everything else is left empty.
```

What the system does:

```
   creates task VN-9, key minted
   creates the task with an empty document
   adds link      affects file comment_service.py
   places it at the root level, since no parent was chosen
   writes a task_created event and a link_added event, origin: user
```

The task now already answers "who is about to touch this file?", from one
question asked at the moment somebody was already thinking about it.

Note what the dialog does **not** offer: a "not sure yet" option. A vague answer
would record a pointer that could never turn green, never collide, and never
verify anything. Somebody who truly does not know writes no link at all, which
is a legitimate state.

The task's location — `app/services/` in the breadcrumb — is not stored anywhere.
It is the container of the one link this task has.

---

## Flow 2 — Plan a task

VN-3 "Add comments" exists as a title and a sentence. Somebody sits down to
plan it.

```
   1. Open VN-3 → the detail panel.

   2. Write the document. Approach, reasoning, what was rejected.
      This is the thinking, and it is the reason the task is not a todo.

   3. Add context links, for the code that has to be understood first:
         ◦ class Post        ◦ class User

   4. Add affects links, including things that do not exist yet:
         + class    Comment                  ← pending, nothing there yet
         + function createComment()          ← pending

   5. Add children, in a sensible reading order:
         1  Comment model
         2  Comment write path
         3  Comment read path
         4  Comment moderation
         5  Show comments on the post page
```

What the system does:

```
   creates five tasks, each with parent_id = VN-3
   assigns each a position, in that order
   indexes the pending creates by name, so duplicates can be found
   draws Comment as a dashed ghost node on the canvas next to app.models
```

At this point nothing has been written in the codebase, and the plan is already
visible in the graph. Anyone opening `app/models` sees a planned class sitting
next to the real ones.

---

## Flow 3 — Find what is ready to start

```
   1. Open the board at the level you are working in.

   2. Read the cards. No filtering needed: blocked and waiting cards carry
      chips, everything else is startable.
```

For the comments example, after links were written but before any dependencies
were added by hand:

```
   READY                             NOT READY
   ─────                             ─────────
   VN-8   Comment model              VN-9   ⚠ waiting — Comment does not exist
   VN-16  Add author to Post         VN-10  ⚠ waiting — Comment does not exist
   VN-5   Write current_user()       VN-12  ⚠ waiting — listComments() missing
```

Nobody wrote a single dependency. The amber chips come from links pointing at
nodes that do not exist yet. This is the cheapest useful thing the whole design
produces, because it needs no coordination at all.

---

## Flow 4 — Accept the suggested dependencies

The amber chips say what is missing. The system also knows who is going to make
it.

```
   1. Open VN-9. The panel shows:

      ⚠ waiting on code
        function app.auth.current_user      VN-5 plans to create this
        class    app.models.Comment         VN-8 plans to create this

        [ add both as dependencies ]   [ not now ]

   2. Click to add them.
```

What the system does:

```
   creates VN-9 ──depends_on──► VN-5
   creates VN-9 ──depends_on──► VN-8
   writes a dependency_added event on each of the three tasks
   VN-9's chip changes from amber "waiting" to red "blocked", naming VN-5
   VN-5 and VN-8 now show "blocks: VN-9"
   VN-3's card shows "1 blocked inside"
```

The difference between amber and red matters. Amber means the code is not
there. Red means somebody has taken responsibility for putting it there.

---

## Flow 5 — Finish a leaf task, and get it checked

```
   1. The work is written. Drag VN-20 "Write createComment()" to Done.

   2. The parser reparses the changed file, as it already does.

   3. On the next read, the pending create link finds a live node with the
      matching name and kind.
```

```
   BEFORE                                AFTER
   ──────                                ─────
   VN-20  ✓ done                         VN-20  ✓ done · verified
   + createComment()   pending           + createComment()   fulfilled
```

If the function had been given a different name, the link would stay pending
and the card would read `done · unverified`, naming what is missing. Candidates
are offered from the nodes created around the same time, and a person confirms.
Nothing binds automatically unless the name and kind match exactly.

---

## Flow 6 — Restructure the tree when the breakdown was wrong

Halfway through executing VN-3, it becomes clear that the original breakdown
does not match the real constraints. VN-8 and VN-9 can be parallelized, and
VN-11 belongs in a different order.

```
   1. On the board for VN-3, drag VN-11 before VN-9 to reorder them.
      
      The position field updates. Everything that depends on order (readiness
      suggestions) recomputes immediately.

   2. Realise VN-8 and VN-9 should both be children of a new grouping task
      VN-25 "Comment data model".
      
      Create VN-25, then reparent VN-8 and VN-9 by dragging them under it.

   3. Update VN-3's document to reflect the new structure. The approach is
      recorded as it now exists.
```

What the system does:

```
   on drag, updates parent_id or position
   writes an event on the moved task: "parent_changed" or "reordered"
   recomputes ready, blocked, progress, rollup on the entire tree
   no task is deleted, no work is lost
```

Everything stays as it was. The structure changes to match reality as people
learn more. The document is the place to record why the structure is what it is.

---

## Flow 7 — Break down a task that turns out to be too big

VN-11 "Comment moderation" was supposed to be one piece, but partway through,
it becomes clear there are two genuinely different ways to do it.

```
   1. Open VN-11. It has no children yet.

   2. Realise there are two genuinely different approaches:
      "Keyword filter" (simple, ships fast)
      "Manual review queue" (better, needs admin page)

   3. Update VN-11's document to describe both approaches and the tradeoff.
      Explain why keyword filter ships first.

   4. Create two children:
         VN-26  Detect banned words          ← part of keyword filter
         VN-27  Hide a comment from the page ← shared by both approaches
      
      VN-27 is already done under the keyword filter.

   5. Assign them to people. VN-26 is ready to start. VN-27 is blocked
      until someone finishes the reading work.
```

What happens:

```
   parent_id on VN-26 and VN-27 points to VN-11
   the board level inside VN-3 now shows VN-11 with "▸ 2 inside" marker
   progress recomputes: VN-11 now shows 1/2 children done
   ready/blocked recomputes: VN-27 knows what it needs from the graph
```

VN-11 was always a task. Adding children to it is the same operation it would
be at any level. The document holds the thinking about why it breaks down
this way and what the tradeoff is.

---

## Flow 8 — Two pieces of work collide

```
   1. Somebody plans VN-30 "Rate limiting":
         ~ affects function createComment()

   2. VN-11's child VN-22 already had:
         ~ affects function createComment()

   3. Immediately, with nobody doing anything:
         the node badge on the canvas turns amber, showing 2
         both cards show  ⚑ contested
         the sidebar contested list gains a row
```

Resolution:

```
   4. Open the conflict panel from either side. Both changes are needed;
      rate limiting is nearly finished.

   5. Choose "decide the order", with VN-30 first, and give a reason.
```

What the system does:

```
   creates VN-22 ──depends_on──► VN-30
   stores a conflict decision recording the reason
   VN-22 now shows  ⛔ blocked — waiting for VN-30
   the node shows   ⏭ sequenced, 2 tasks
   the contested list moves the row into a quieter sequenced section
```

When VN-30 moves to done, VN-22 becomes ready everywhere at once, because
readiness was never stored.

---

## Flow 9 — A rename breaks a link

Somebody renames `renderPost` to `render_post_page`. The parser deletes the old
node and creates a new one.

```
   VN-12  Show comments on the post page
   ┌────────────────────────────────────────────────────────┐
   │ ⚠ affects  function app.web.renderPost                   │
   │   this node no longer exists in the graph               │
   │   closest matches:                                       │
   │     ƒ app.web.render_post_page        same file, similar │
   │     ƒ app.web.render_post_list        same file          │
   │   [ point at the first ]  [ search ]  [ remove the link ]│
   └────────────────────────────────────────────────────────┘
```

The person clicks the first match. One operation moves the link, keeping its
mode and note, and writes a link_added event recording the repair.

Nothing was repaired automatically, because a silent move changes what the plan
means. The warning is visible and the fix is one click, which is the right
balance.

---

## Flow 10 — Close out a parent

VN-3 "Add comments" is finished, except that moderation was cut from this
release.

```
   1. Drag VN-3 to Done.

   2. The system notices two children are not finished and asks:

      ┌───────────────────────────────────────────────────────────┐
      │  Two tasks inside VN-3 are still open:                     │
      │     VN-11  Comment moderation      to do                   │
      │     VN-22  Detect banned words     to do                   │
      │                                                            │
      │   ○ Mark them done as well                                 │
      │   ● Leave them open — they will be picked up separately    │
      │   ○ Cancel                                                 │
      └───────────────────────────────────────────────────────────┘

   3. Choose to leave them open.
```

What the system does:

```
   moves VN-3 to done
   writes a status_changed event recording that 2 children were left open
   VN-3's card shows  ✓ done · 3 of 5 · 2 left open
   VN-11 and VN-22 stay where they are, still visible inside VN-3
   VN-3's create links are checked: everything it promised exists  ⇒ verified
```

The record explains itself a year later. A person seeing `3 of 5` on a finished
task can read the note and find out that the remaining work was deliberately
deferred rather than forgotten.

---

## What these ten flows exercise

```
   creation from the graph                 flow 1
   documents, context, affects, children   flow 2
   readiness with no coordination          flow 3
   suggested dependencies                  flow 4
   verification against the graph          flow 5
   changing approach without losing work   flow 6
   growth at any depth                     flow 7
   conflict, resolved by ordering          flow 8
   graph drift and repair                  flow 9
   closing work honestly                   flow 10
```

The next file, [14 — Edge cases](14-edge-cases.md), deliberately tries to break
what these flows assume.
