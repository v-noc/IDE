# 11 — Interface Surfaces

The model only works if the screens make it obvious. A recursive tree with
versions and modes could easily produce an interface where nobody knows what
level they are on or which approach they are reading. This file describes each
surface, what it shows, and the rules that keep it honest.

The layouts below are sketches of information, not visual design.

---

## 1. The level board

The board shows the children of one task, in columns by status. It never shows
two levels at once.

```
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  ▸ root ▸ Add comments                        [pin this level]  [ All ▾] │
  │  VN-3 · in progress · 3 of 5 done · 1 blocked inside                     │
  ├────────────────┬────────────────┬────────────────┬─────────────────────┤
  │  TO DO         │  IN PROGRESS   │  IN REVIEW     │  DONE               │
  ├────────────────┼────────────────┼────────────────┼─────────────────────┤
  │ ┌────────────┐ │ ┌────────────┐ │                │ ┌─────────────────┐ │
  │ │VN-10       │ │ │VN-9        │ │                │ │VN-8             │ │
  │ │Comment read│ │ │Comment     │ │                │ │Comment model    │ │
  │ │path        │ │ │write path  │ │                │ │✓ verified       │ │
  │ │⛔ VN-8      │ │ │⚑ contested │ │                │ └─────────────────┘ │
  │ └────────────┘ │ └────────────┘ │                │                     │
  │ ┌────────────┐ │                │                │                     │
  │ │VN-11       │ │                │                │                     │
  │ │Moderation  │ │                │                │                     │
  │ │⑂ 2 versions│ │                │                │                     │
  │ │▸ 2 inside  │ │                │                │                     │
  │ └────────────┘ │                │                │                     │
  └────────────────┴────────────────┴────────────────┴─────────────────────┘
```

**The header carries the level.** The breadcrumb says where you are, and the
line under it summarises the task whose children you are looking at. At the
root the breadcrumb is just `root` and the summary line is the project.

**Clicking a card opens the detail panel. Clicking the `▸ n inside` marker
descends a level.** These are two different gestures because they are two
different intentions, and merging them would make it impossible to read a task
without losing your place.

**Cards carry conditions, not just status.** A card shows at most three
markers, in this order of importance: blocked, contested, and how many tasks
are inside it. More than three markers on a card and people stop reading any of
them.

### Pinning a level

Somebody working inside one area for a week pins that level. The board then
opens there, and the breadcrumb shows that the root is pinned with one click to
release it. This is a per-tab setting, like the existing history scope.

### The root level

The root shows every task that no active version refers to. That means new
tasks nobody has placed yet and orphans left behind when an approach changed.
Both need attention, so both are visible, and orphans carry a grey chip
explaining why they are there.

**Tradeoff.** The root can accumulate orphans over months. The answer is a
filter, not automatic cleanup, because deleting somebody's work because it fell
out of a plan is the one thing this design never does.

---

## 2. The list view

The same level, as rows instead of cards, for people who want density and for
planning rather than execution.

```
  ▸ root ▸ Add comments
  ┌───────┬────────────────────────┬──────────┬─────────────────┬──────────┐
  │ VN-8  │ Comment model          │ done ✓   │ creates Comment │          │
  │ VN-9  │ Comment write path     │ doing    │ ⚑ contested     │ ⛔ VN-5   │
  │ VN-10 │ Comment read path      │ to do    │                 │ ⛔ VN-8   │
  │ VN-11 │ Comment moderation     │ to do    │ ⑂ 2 versions    │ ▸ 2      │
  │ VN-12 │ Show comments on page  │ to do    │ modifies render │          │
  └───────┴────────────────────────┴──────────┴─────────────────┴──────────┘
```

The list view is also where the **order of the version's children** is visible
and editable by dragging, since that order is reading advice and belongs with
planning rather than with execution.

---

## 3. The task detail panel

Opens in the right slot, over whatever is on the canvas, so the graph stays
visible.

```
  ┌────────────────────────────────────────────────────────────────┐
  │ VN-9   Comment write path                              ✕       │
  │ ▸ root ▸ Add comments ▸ VN-9                                   │
  │ in progress · high · comments, backend                         │
  ├────────────────────────────────────────────────────────────────┤
  │ ⛔ blocked — VN-5 "Write current_user()" is not done            │
  │ ⚑ contested — createComment() also modified by VN-30           │
  ├────────────────────────────────────────────────────────────────┤
  │ Saving a comment needs one function that validates the post,   │
  │ attaches the author, and stores the row.                       │
  ├────────────────────────────────────────────────────────────────┤
  │ DOCUMENT                                        [edit]          │
  │ ## Approach                                                     │
  │ The service layer owns validation, the repository owns …        │
  │                                                    [show all]   │
  ├────────────────────────────────────────────────────────────────┤
  │ CONTEXT                                            [+ add]      │
  │   ◦ class    Post                     live                      │
  │   ◦ class    User                     live                      │
  │   ◦ function current_user()           ⚠ does not exist yet      │
  │                                                                 │
  │ AFFECTS                                            [+ add]      │
  │   + function createComment()          pending                   │
  │   ~ class    Comment                  live      ⚑ contested     │
  ├────────────────────────────────────────────────────────────────┤
  │ CHILDREN  1 of 2                                  [+ add]       │
  │   1 ✓ VN-20  Write createComment()                              │
  │   2 ○ VN-21  Validate that the post exists                      │
  ├────────────────────────────────────────────────────────────────┤
  │ DEPENDS ON            VN-5  ▸ Auth ▸ Sessions ▸ VN-5   ⛔        │
  │ BLOCKS                VN-10 Comment read path                   │
  ├────────────────────────────────────────────────────────────────┤
  │ ACTIVITY                                                        │
  │   moved to in progress · 2 days ago                             │
  │   linked class Comment as modify · 3 days ago                   │
  └────────────────────────────────────────────────────────────────┘
```

Four rules govern this panel.

**Conditions sit at the top, above everything.** If a task is blocked or
contested, that is the first thing a person needs, before the description and
long before the document.

**Context and Affects are separate lists, with the mode shown as a symbol.**
`◦` for read, `+` for create, `~` for modify, `−` for delete. Each row shows
the link's computed state, so a pending create and a missing dependency look
different at a glance.

**Children show their position and their state.** The number is the version's
reading order, and it can be dragged.

**Dependencies show breadcrumbs.** A blocker four levels away in another part
of the tree is useless without knowing where it lives.

### The document

The document is the long write-up and it is the reason a task is more than a
todo. In the panel it is collapsed to a few lines with a way to expand, and it
opens into a full width editor when somebody is actually writing.

It is markdown, it lives in the same versioned database as everything else, so
its history comes from commits, and mentions of a task key or a node name
become links.

---

## 4. Versions in the interface

While a task has one version, the word never appears. The document, the lists,
and the children are simply the task's.

The moment a second version exists, a switcher appears in the panel header:

```
  ┌────────────────────────────────────────────────────────────────┐
  │ VN-11  Comment moderation                              ✕       │
  │ ▸ root ▸ Add comments ▸ VN-11                                  │
  │ ⑂ v1 Keyword filter ★active   |   v2 Manual review queue       │
  │                                        [compare]  [new version]│
```

Reading a version that is not active changes everything below the header, and
the panel says so plainly with a band across the top:

```
  │ ⚠ you are reading v2, which is a draft. It is not the plan.     │
```

Without that band, somebody edits a draft believing it is the plan, and the
model's cheapest feature becomes its most dangerous one.

### Comparison

```
  ┌──────────────────────────┬──────────────────────────────────────┐
  │ v1  Separate Comment class│ v2  Comments inside Post             │
  ├──────────────────────────┼──────────────────────────────────────┤
  │ creates  class Comment    │ creates  —                           │
  │          fn createComment │                                      │
  │ modifies fn renderPost    │ modifies class Post ⚑ 2 tasks read it│
  │ children 5                │ children 2                           │
  │          VN-12 shared ────┼──────── VN-12 shared                 │
  └──────────────────────────┴──────────────────────────────────────┘
                        [ activate v2 ]
```

The link rows are what decide arguments, because they show real consequences.
Here, one approach adds new code while the other rewrites a class that two
other tasks are already reading, and that fact appears without anybody
analysing anything.

---

## 5. On the canvas

The graph is where this product is different, so work has to be visible there.

```
   ┌──────────────────────────────┐
   │ ƒ createComment()        ⚑2  │   ← amber badge: contested
   ├──────────────────────────────┤
   │ ⋯                            │
   └──────────────────────────────┘

   ┌──────────────────────────────┐
   │ ◇ Comment                 ◌  │   ← dashed outline: planned, not built yet
   └──────────────────────────────┘
```

**A badge on a node** shows how many open tasks link to it. Amber when
contested, grey otherwise.

**Planned nodes appear as ghosts.** A `create` link names a node that does not
exist, so the canvas can draw it as a dashed placeholder next to its intended
parent. This is the most direct expression of the whole design: *the plan is
visible in the graph before the code is written.*

**Clicking a badge opens the node popover:**

```
  ┌──────────────────────────────────────────────┐
  │ ƒ app.services.createComment                 │
  │ ⚑ 2 open tasks intend to modify this         │
  ├──────────────────────────────────────────────┤
  │ ~ VN-30  Rate limiting          in progress  │
  │ ~ VN-11  Comment moderation     to do        │
  │ ◦ VN-40  Audit logging          to do        │
  ├──────────────────────────────────────────────┤
  │ [ resolve the conflict ]   [ new task here ] │
  └──────────────────────────────────────────────┘
```

**Task lens** stays as it is today: focusing a task dims the canvas except the
nodes it touches. With modes, the lens can colour them, so created nodes,
modified nodes, and context read differently. A person can see the shape of the
work before doing it.

---

## 6. The sidebar

Two additions to what exists.

**Work tree.** The task tree, collapsible, showing the whole structure rather
than one level. This is where you see across levels, which the board
deliberately does not do.

**Contested nodes.** A ranked list of nodes that more than one open task
intends to write, worst first. Clicking one focuses it on the canvas and opens
the popover. This replaces and sharpens the existing blockers section.

```
  ┌──────────────────────────────┐
  │ CONTESTED                    │
  │ ⚑ createComment()         2  │
  │ ⚑ class Post              2  │
  │ ⏭ renderPost()      sequenced│
  └──────────────────────────────┘
```

Sequenced pairs are shown differently rather than hidden, so a person can see
that a situation was handled rather than wondering whether it was noticed.

---

## 7. Creating work from the graph

The cheapest way to get good links is to create tasks from the place the work
is about.

```
   right-click a node ─────► New task here
                             the task opens with an anchor already set
                             and one link prefilled, mode asked once:
                             "will this work read it, change it, or remove it?"
```

That single question at creation time is where most links come from. Asking it
once, at the moment somebody is already thinking about that node, costs nothing
and produces the data every derived feature depends on.

---

## 8. Rules the interface must follow

These are the ones that prevent the model from becoming confusing.

| Rule | Why |
|---|---|
| Always show the current level in a breadcrumb | The board shows one level, so the level must never be ambiguous |
| Always name the version when showing version content, once a second version exists | Editing a draft while believing it is the plan is the worst mistake available |
| Never show more than three condition markers on a card | Beyond three, people stop reading all of them |
| Blocked and contested chips always name the other side | A warning that does not say who or what is noise |
| Orphaned means a grey chip and an explanation, never disappearance | Work that silently vanishes destroys trust in the whole tool |
| Empty Affects is not a warning | Documentation and configuration work has no graph trace, and that is fine |
| Derived values never appear editable | If a person can click on "blocked", they will expect it to change something |

The next file, [12 — Agent seams](12-agent-seams.md), covers what an agent needs
from this model, without designing the agent.
