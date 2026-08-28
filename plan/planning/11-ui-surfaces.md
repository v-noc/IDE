# 11 — Interface Surfaces

The model only works if the screens make it obvious. A recursive tree with link
modes could easily produce an interface where nobody knows what level they are
on or what a marker means. This file describes each surface, what it shows, and
the rules that keep it honest.

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
  │ │▸ 2 inside  │ │                │                │                     │
  │ │🔴 1 blocked │ │                │                │                     │
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

The root shows every task `where parent_id is null`. A brand new task nobody has
placed yet and a deliberate top-level goal are the same thing, which is now
correct rather than a conflation — there is no orphan section, because there are
no orphans.

Deleted tasks never appear. Every read filters `deleted_at is null`, and a
restore brings a whole subtree back at once.

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
  │ VN-11 │ Comment moderation     │ to do    │                 │ ▸ 2      │
  │ VN-12 │ Show comments on page  │ to do    │ affects render │          │
  └───────┴────────────────────────┴──────────┴─────────────────┴──────────┘
```

The list view is also where **sibling order** is visible and editable by
dragging. Dragging writes a new `position`, which is reading advice and belongs
with planning rather than with execution.

---

## 3. The task detail panel

Opens in the right slot, over whatever is on the canvas, so the graph stays
visible.

```
  ┌────────────────────────────────────────────────────────────────┐
  │ VN-9   Comment write path                              ✕       │
  │ ▸ root ▸ Add comments ▸ VN-9                                   │
  │ in progress · high · comments, backend                         │
  │ 📍 app/services/comment_service.py          ← derived location  │
  ├────────────────────────────────────────────────────────────────┤
  │ ⛔ blocked — VN-5 "Write current_user()" is not done            │
  │ ⚑ contested — createComment() also affected by VN-30           │
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
  │   linked class Comment as affects · 3 days ago                   │
  └────────────────────────────────────────────────────────────────┘
```

Five rules govern this panel.

**Conditions sit at the top, above everything.** If a task is blocked or
contested, that is the first thing a person needs, before the description and
long before the document.

**The location line is derived and must never look editable.** It is the nearest
container holding every linked node. When that container is too broad to be
useful — a top-level folder, or the repository — the line is replaced by the
count of linked nodes rather than showing something meaningless:

```
   📍 app/services/comment_service.py        one file holds everything
   📍 class Comment                          one class holds everything
   📍 6 nodes across 3 files                 nearest container was app/, too broad
```

There is no field behind this line. A person who wants to change it changes the
links, which is the honest relationship: where the work lives *is* which code it
touches.

**Context and Affects are separate lists, with the mode shown as a symbol.**
`◦` for read, `+` for create, `~` for affects, `−` for delete. Each row shows
the link's computed state, so a pending create and a missing dependency look
different at a glance.

There are only these four. A link never says merely "this task is about this
node", so no row in either list is exempt from having a state.

**Children show their position and their state.** The number is the sibling
order from `position`, and it can be dragged.

**Dependencies show breadcrumbs, in both directions.** The panel lists what this
task depends on *and* what depends on it. A blocker four levels away in another
part of the tree is useless without knowing where it lives, and the reverse list
matters more than it used to: with a single parent, a genuinely shared step
lives under one parent and every other interested task sees it only as a
dependency. Without the reverse list, that relationship is invisible from one
end.

### The document

The document is the long write-up and it is the reason a task is more than a
todo. In the panel it is collapsed to a few lines with a way to expand, and it
opens into a full width editor when somebody is actually writing.

It is markdown, it lives in the same database as everything else, so its history
comes from commits, and mentions of a task key or a node name become links.

The document is also where **alternatives** live. There is no version switcher,
because there are no versions: two competing approaches are two sections of one
write-up, or a separate proposal task whose children get moved under the real
task if it is accepted.

---

## 4. On the canvas

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
  │ ⚑ 2 open tasks intend to change this          │
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
affected nodes, and context read differently. A person can see the shape of the
work before doing it.

---

## 5. The sidebar

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

## 6. Creating work from the graph

The cheapest way to get good links is to create tasks from the place the work
is about.

```
   right-click a node ─────► New task here
                             the task opens with one link prefilled,
                             mode asked once:
                             "will this work read it, change it, or remove it?"
```

That single question at creation time is where most links come from. Asking it
once, at the moment somebody is already thinking about that node, costs nothing
and produces the data every derived feature depends on.

There is no "not sure yet" option. A fourth, vague answer would record a pointer
nothing downstream can use — it would never turn green, never warn anybody, and
never mark anything done. Three concrete choices at the moment of most context
is the better trade, and a wrong choice is visible and correctable later against
the commits.

Somebody who genuinely does not know yet writes no link. An empty Affects list
is a legitimate state, not a gap to be filled with something meaningless.

---

## 7. Rules the interface must follow

These are the ones that prevent the model from becoming confusing.

| Rule | Why |
|---|---|
| Always show the current level in a breadcrumb | The board shows one level, so the level must never be ambiguous |
| Never show more than three condition markers on a card | Beyond three, people stop reading all of them |
| Blocked and contested chips always name the other side | A warning that does not say who or what is noise |
| A cascade delete always names its blast radius before it happens | Work that silently vanishes destroys trust in the whole tool |
| Empty Affects is not a warning | Documentation and configuration work has no graph trace, and that is fine |
| The location line never looks editable | It is derived from the links; an editable-looking field invites somebody to set it independently and then wonder why it drifts |
| A container's derived involvement is styled differently from a typed link | "This class contains work" and "this class changes" are different claims, and only the second one is verified |
| Derived values never appear editable | If a person can click on "blocked", they will expect it to change something |

The next file, [12 — Agent seams](12-agent-seams.md), covers what an agent needs
from this model, without designing the agent.
