# 04 — Lifecycle and Status

This file covers how a task moves through its life, and what the word "done"
means when work is a tree instead of a flat list.

There are two separate things that people usually confuse, and keeping them
apart makes the rest simple.

```
   STATUS            chosen by a person. Which column the card is in.
                     backlog · to do · in progress · in review · done

   CONDITION         computed by the system. Whether the work can proceed.
                     blocked · waiting on code · ready · contested · verified
```

Status is a decision. Condition is a fact. A card in the "to do" column can be
blocked, and a card in "in progress" can be waiting on code. The two never
overwrite each other, and the interface shows both at once.

---

## 1. Task status

Status is unchanged from the current system. It is the id of a board column,
and columns are configurable, with two flags that give them meaning: one says
the column counts as done, and one marks the single backlog column.

```
   ┌──────────┐   ┌────────┐   ┌──────────────┐   ┌───────────┐   ┌────────┐
   │ backlog  │──►│ to do  │──►│ in progress  │──►│ in review │──►│  done  │
   └──────────┘   └────────┘   └──────────────┘   └───────────┘   └────────┘
        ▲              ▲               │                │              │
        └──────────────┴───────────────┴────────────────┴──────────────┘
                     any move is allowed, in any direction
```

The system does not enforce a path through the columns. People move cards
backwards for good reasons, and a tool that argues about it just gets worked
around. What the system does instead is **notice** and say something useful,
which is covered in section 4.

---

## 2. Condition: what the system computes

Every task carries a computed condition alongside its status. Conditions are
never stored, because every one of them can change without anybody touching
the task: somebody else finishes their work, a reparse deletes a node, a task
is moved in another part of the tree.

| Condition | True when | Shown as |
|---|---|---|
| `blocked` | Something in `depends_on` is not finished | red chip naming the blocker |
| `waiting on code` | A `read`, `affects`, or `delete` link points at a node that does not exist yet | amber chip naming the node |
| `ready` | Neither of the above | no chip |
| `contested` | Another open task intends to write a node this one writes | amber chip on the card and the node |
| `verified` | Every `create` link now points at a node that really exists | green tick next to done |
| `blocked below` | Some descendant is blocked, even though this task is not | small red dot with a count |

An example of the two layers together:

```
   ┌────────────────────────────────────────────────┐
   │ VN-9   Comment write path         ● in progress│   ← status, chosen
   │ ⛔ blocked — waiting for VN-5 current_user()   │   ← condition, computed
   │ ⚑ contested — createComment() also in VN-30    │   ← condition, computed
   └────────────────────────────────────────────────┘
```

Nothing prevents somebody working on a blocked task. The chip is information,
not a lock. There is exactly one place where the system pushes back, which is
marking something done, and even there it asks rather than refuses.

---

## 3. What "done" means

Done means something slightly different at each level, and the system is
explicit about which meaning applies.

### A leaf task is done when the person says so

A task with no children is done when somebody moves it to a done column. The
system does not argue, but it does check the claim against the graph.

```
   VN-20  "Write createComment()"      moved to done
     create link ──► function app.services.createComment

   The graph now contains that function.
     ⇒ done ✓ verified
```

If the function is not there, the task is still done, because the person said
so and they may have good reason. It is shown as **done, unverified**, with the
missing item named.

```
   ┌──────────────────────────────────────────────────────┐
   │ VN-20  Write createComment()              ✓ done     │
   │ ⚠ unverified — createComment() is not in the graph   │
   └──────────────────────────────────────────────────────┘
```

This is the payoff of linking work to a real graph. In a sentence based todo
list, "done" is a claim nobody can check. Here it is a claim the system quietly
checks and reports on, without ever blocking anybody.

**Tradeoff.** Some real work has no graph trace at all: writing documentation,
changing configuration, having a conversation. Those tasks have no `create`
links, so they are simply done with nothing to verify. The absence of
verification is not a warning, and the interface must not treat it as one.

### A parent task is done when its work is done

A parent has children, and its children are its work, so marking a parent done
while children are open is usually a mistake. Usually, not always: sometimes
the remaining children turn out to be unnecessary.

So the system asks instead of refusing.

```
   Moving VN-3 "Add comments" to done, with 2 of 5 children unfinished.

   ┌───────────────────────────────────────────────────────────┐
   │  Three of these are still open:                            │
   │     VN-11  Comment moderation        to do                 │
   │     VN-12  Show comments on page     in progress           │
   │                                                            │
   │  What should happen to them?                               │
   │    ○ Mark them done as well                                │
   │    ○ Leave them open, they will be picked up separately    │
   │    ○ Cancel                                                │
   └───────────────────────────────────────────────────────────┘
```

Whatever is chosen becomes an event on the parent, so the record explains itself
later.

### A tree is finished when nothing inside it is open

Progress on a parent is counted over its **direct children**, and it is shown as
a simple fraction on the card.

```
   VN-3  Add comments        3/5        ← direct children of VN-3
   VN-3  Add comments        3/5 · 11/17 deep   ← optional deep count
```

The direct count is the honest default, because it matches what you see when
you open that level of the board. The deep count is available for people who
want it, and it always states that it is deep, so the two numbers are never
confused.

---

## 4. How condition rolls up the tree

Blocking is the one condition that must travel upward, because a person looking
at a high level card needs to know that something inside is stuck, without
opening every level.

```
   VN-3  Add comments                          ● in progress   3/5   🔴 1
     ├── VN-8   Comment model                  ✓ done
     ├── VN-9   Comment write path             ● in progress   ⛔ blocked by VN-5
     ├── VN-10  Comment read path              ○ to do
     ├── VN-11  Comment moderation             ○ to do
     └── VN-12  Show comments on the post page ○ to do
```

The red dot with a `1` on the parent means one task inside is blocked. Clicking
it opens the exact task rather than making somebody hunt for it. The parent is
not itself marked blocked, because that would be false: nothing prevents VN-3
as a whole from progressing, since three of its five children are free to move.

The same rollup applies to contested nodes and to unverified done, each with
its own small marker. Nothing else rolls up, because a parent covered in chips
tells you nothing.

**Tradeoff.** Rollup means a read of one card touches its whole subtree. This is
the main cost of the recursive model, and [09 — Architecture](09-architecture.md)
handles it by computing one summary for the whole board level in a single pass
instead of per card.

---

## 5. Reopening, and moving backwards

A task can move from done back to any other column. When that happens, three
things follow automatically.

```
   VN-5  "Write current_user()"   done ──► in progress

   1. A note is written on VN-5.
   2. Every task that depends on VN-5 becomes blocked again, immediately,
      because blocking is computed and not stored.
   3. Parents recompute their progress and their rollup markers.
```

Nobody has to remember to update anything, and there is no possibility of a
stale "blocked" flag on the other side, because there was never a flag.

---

## 6. The full picture

```
   TASK VN-9  "Comment write path"

   STATUS      in progress                  ← a person moved it here
   ├ blocked          yes, VN-5 unfinished  ← computed from depends_on
   ├ waiting on code  yes, current_user()   ← computed from link states
   ├ contested        yes, createComment()  ← computed from other tasks' links
   ├ progress         1 of 2 children       ← computed from direct children
   └ verified         not yet, 1 create link pending

   STORED DATA
   ├ document       "Service layer owns validation…"
   ├ children       VN-20 ✓ done · VN-21 ○ to do
   └ links          read Post · read current_user() · create createComment()
```

Everything on the left of that picture is stored. Everything indented under it
is worked out at the moment somebody looks.

The next file, [05 — Graph links](05-graph-links.md), goes deeper into the part
that makes all of this checkable: how work points at code, what happens when
the code is not there yet, and what happens when the parser deletes it.
