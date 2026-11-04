# Planning System — Recursive Tasks on Top of the Code Graph

This folder holds the design for V-NOC's planning layer. The planning layer is
the part of the product that turns a vague wish like "we should let people
comment on posts" into a structured piece of work that a human can read, that a
board can display, and that later an agent can execute step by step.

This is a design folder, not an implementation folder. There is no code here,
there are no database migrations, and there are no final API signatures. What
you will find instead is the complete thinking: what each concept means, why it
exists, what it costs, how the pieces relate to each other, what happens in the
awkward cases, and a full worked example that runs the whole model from an
empty board to finished work.

## Why this design exists

The project already has a simple task system. It has tasks, it has subtasks, it
has blockers, and it can already connect a task to nodes in the code graph. That
is a genuinely good starting point, and this design builds on it rather than
replacing it.

The problem is that the current system can only record *what* somebody wants.
It cannot record *how* the work will be done, it cannot hold two competing
ideas about how to do it, it cannot say which classes and functions each step
will read or rewrite, and it cannot warn you when two people are about to
change the same function at the same time. Those are exactly the things you
need in place before a planning agent becomes useful, because an agent needs an
ordered, scoped, checkable work list rather than a paragraph of prose.

Coding agents today, including Claude Code and Cursor, keep a todo list made of
sentences. The list is useful while the session runs, and then it disappears,
and nobody can verify afterwards that the sentences were true. V-NOC has
something those tools do not have, which is a real graph of the code. When a
piece of work says "this step creates the `Comment` class", the graph can be
asked afterwards whether that class actually exists now. Planning on top of a
graph should make claims checkable instead of merely believable, and that is
the reason to build this rather than copying a todo list.

## The single most important decision

Everything in this folder follows from one decision: **a task has exactly one
parent. No shared children, no task appearing in two places at once.**

This simplifies everything. Because a task can only exist in one place in the
tree, you can delete a parent and know exactly what disappears — the whole
subtree below it. You can move a task by changing one field on the child. When
two pieces of work would share a step, one of them now depends on the other
instead, which is honest: dependencies are the right tool for shared work.

A task owns its document and its link plan directly. There is no separate
version object, no choice of "active" approach, and no rewriting to recover
lost work. The model is simpler to understand, simpler to store, and because
child ordering is explicit and deterministic, there is no orphan concept at all.

```
   TASK ───────────────────────────────────
     │
     │  identity and intent:
     │     key · title · description · type
     │     status · priority · labels
     │     parent_id (null = root level)
     │     position (order among siblings)
     │
     │  the approach and its trace:
     │     document · node_links[] · depends_on[]
     │
     │  ordered list of CHILD TASKS via:
     │     parent_id = this.id + order by position
     │
     └── and every child is ... a TASK
```

The word *subtask* still exists, but only as a way of speaking. A subtask is
simply a task whose `parent_id` points to another task. It is a position in the
tree, not a different kind of thing, so a subtask has every capability a task
has: its own description, its own document, its own children, and its own place
on the board.

## What a task carries

A task is not a one-line todo. It is meant to be the place where the thinking
about a piece of work lives, so it carries a short description for the board
and a long document for the detail.

```
   ┌─ TASK  VN-9  "Comment write path" ────────────────────────────────┐
   │                                                                    │
   │  title        Comment write path                                   │
   │  description  One paragraph. What this work is and why it matters. │
   │               This is what the board card shows.                   │
   │                                                                    │
   │  document     The long write-up. The approach, the reasoning, the  │
   │               things that were considered and rejected, the shape  │
   │               of the code, anything a reader needs. Markdown.      │
   │                                                                    │
   │  context      Nodes you must read to do this work, but will not    │
   │               change. Optional.                                    │
   │                 class Post · class User · function current_user()  │
   │                                                                    │
   │  affects      Nodes this work will create, change, or delete.      │
   │                 create   function createComment()                  │
   │                 affects  class Comment                             │
   │                                                                    │
   │  children     Ordered list of child tasks, if it has any.          │
   │  depends_on   Other tasks that must finish first.                  │
   │  status       Which board column it is in.                         │
   └────────────────────────────────────────────────────────────────────┘
```

Context nodes and affected nodes are the same mechanism seen from two sides.
Both are links from the task into the code graph, and each link carries a mode
that says what the work does to that node. Modes that only read become the
Context list on screen, and modes that write become the Affects list. Keeping
one mechanism underneath means a single query answers "what work touches this
node", while the two lists on screen keep the reading experience clear.

There are four modes — `read`, `create`, `affects`, `delete` — and **none of
them is vague**. Every link states something the graph can later confirm or
contradict.

Which means a task never states where it lives. That is derived from the links —
the nearest container holding all of them — so the location can never drift out
of step with the code the work actually touches.

## How the shape maps onto the code graph

This is not a coincidence, and it is worth noticing early. The code graph in
this product is already recursive. A folder holds files, a file holds classes,
a class holds functions, and a function holds calls. The work tree is now
recursive in exactly the same way, which means the same navigation gestures,
the same breadcrumbs, the same idea of zooming in one level, and the same kind
of database query serve both trees.

```
   CODE TREE                        WORK TREE
   ─────────                        ─────────
   folder  app/                     task    Add comments
     file    models.py                task    Comment model
       class   Post                     task    Add author_id field
         function  createPost()       task    Comment write path
           call    save()               task    Write createComment()
```

There is one rule about the code side that never bends, and every document in
this folder respects it:

> **The graph has exactly five node kinds, which are folder, file, class,
> function, and call. A field is not a node. A column is not a node. A
> parameter is not a node. An endpoint is not a node.**

When a piece of work is about a field, the work links to the class or the
function that contains that field, and the field itself is described in the
task's own words. A task titled "Add an `author_id` field to Comment" links to
the **class** `Comment` with mode `affects`, and the sentence carries the
detail. This keeps the planning layer honest about what the parser actually
produces, and it means no plan can ever point at a node kind that cannot exist.

## What the board looks like

A recursive work tree could easily produce a board with two hundred cards on
it, which would be far worse than what exists today. The board avoids this by
showing **one level at a time**, in the same way a file explorer does.

```
   BOARD AT THE ROOT                    BOARD INSIDE "Comments"
   ┌──────┬─────────┬──────┐            ▸ Comments ▸
   │ todo │ doing   │ done │            ┌──────────┬──────────┬────────┐
   │      │         │      │            │ todo     │ doing    │ done   │
   ├──────┼─────────┼──────┤            ├──────────┼──────────┼────────┤
   │VN-3  │ VN-1    │ VN-2 │   click    │ VN-10    │ VN-9     │ VN-8   │
   │Comm… │ Auth    │Posts │   VN-3 ──► │ read path│ write    │ model  │
   │1/5   │ 2/3     │      │            │ VN-11    │          │        │
   └──────┴─────────┴──────┘            │ moderat… │          │        │
                                        └──────────┴──────────┴────────┘
```

You start at the root and see three cards, which is an honest summary of the
whole project. You open one card and the board becomes that card's children. A
breadcrumb takes you back up. If you are going to live inside one area for a
week, you pin that level as your board root and the rest of the tree stops
distracting you. Detail never floods the board, because detail is always one
level down rather than on the same screen.

## Reading order

Each file goes one step further from the general idea toward the specific
mechanics. If you read them in order, every file only uses ideas that an
earlier file has already explained.

**If you only read one file, read [rules.md](rules.md).** It is the normative
artifact: the three stored edges, the full derived table, the guards, and the
invariants. Everything else in this folder is the rationale behind it.

```
plan/planning/
│
├── rules.md                          ◄── THE SPEC. One page. Start here.
│      The three stored edges, everything derived, the guards, and the
│      invariant list that the tests must enforce.
│
├── 00-mental-model.md
│      The idea in full. What a task is, why work is recursive, how deep a
│      tree should go, and the tradeoffs this shape brings.
│
├── 01-concepts.md
│      Careful definitions of Task, Parent and position, Node link,
│      Dependency, and Event, including what each one is NOT.
│
├── 02-relationships.md
│      The relationship catalog. Three stored edges — parent, depends_on, and
│      node links with a mode — what each derives, and the gate a fourth
│      would have to pass.
│
├── 03-data-model.md
│      Every field of every entity in tables, split clearly into what is
│      stored and what is computed at read time.
│
├── 04-lifecycle-and-status.md
│      Status versus condition, how progress rolls up the tree, and what the
│      word "done" means at each level.
│
├── 05-graph-links.md
│      How work points at code: the four link modes, links that point at code
│      which does not exist yet, binding and rebinding, verification stamped
│      with a graph revision, link rollup, and the two lookup directions.
│
├── 06-dependencies-and-readiness.md
│      The dependency design in full: one stored edge, dependencies at any
│      depth, the asymmetric guard, and why readiness is computed from needs
│      rather than from position in a list.
│
├── 08-conflicts-and-concurrency.md
│      Two pieces of work, one node. The mode matrix, the difference between
│      overlap, watch, and conflict, and how a human decision about a
│      collision is recorded without corrupting the data.
│
├── 09-architecture.md
│      Where truth lives, the three storage categories, the single evaluation
│      function every derived value comes from, batching, and what is
│      deliberately kept out of storage.
│
├── 10-api-surface.md
│      The operation catalog in plain language: every read, every write, and
│      the guarantee each one makes.
│
├── 11-ui-surfaces.md
│      The level board, the task detail panel, the document editor, the child
│      list, the node popover, the sidebar, and the canvas overlays.
│
├── 12-agent-seams.md
│      How an agent would read a task, propose a plan, and execute work,
│      described only as the seams the model must leave open. The agent itself
│      is not designed here.
│
├── 13-flows.md
│      Step-by-step walkthroughs of the ten situations that happen most often.
│
├── 14-edge-cases.md
│      Twenty-two deliberate attempts to break the model, each with the model's
│      answer, and an honest note whenever the answer is merely acceptable.
│
├── 15-migration-from-today.md
│      What exists in the codebase right now, what changes, the migration
│      steps, and the P0–P3 build order.
│
├── 16-open-questions.md
│      The questions this pass did not settle, with the options for each.
│
└── examples/social-media/
       The entire model applied to a small social media application, from an
       empty board through three tasks, cross-tree dependencies, a conflict,
       and every list the system can produce.
```

> **Note.** `07-versions-and-alternatives.md` was deleted when versions were
> removed from the model, which is why the numbering skips from 06 to 08. The
> remaining files keep their original numbers so existing links do not break.

## The principles used while designing this

**Fewer relationship types beat more of them.** Every relationship type you add
is a question the user has to answer correctly for the rest of the product's
life. If two relationship types can be confused with each other, the database
fills up with data that means nothing. This design stores three relationships
and computes everything else.

**Store the decisions people make, and compute the facts.** Whether a node is
being fought over by two pieces of work is a fact, so the system computes it
fresh on every read. Whether a team agreed to ignore that fight is a decision,
so the system stores it.

**Every pointer must make a checkable claim.** A link that only says "this task
has something to do with this node" looks like data and behaves like a comment:
nothing downstream can verify it, warn on it, or ever mark it done. Each of the
four modes states something the graph can later confirm or contradict. If a link
cannot be wrong, it cannot be useful.

**Point hard references at durable things and soft references at fragile
ones.** Task to task links can be real database links, because a task only
disappears when a person deletes it. Links from a task into the code graph must
stay soft, because the parser deletes and recreates graph nodes whenever a file
changes. A soft link that loses its target becomes a visible warning, which is
useful, instead of a broken record, which is not.

**Let the graph be the judge.** A checkbox is only a claim that something was
done. Because every task names the nodes it will create or change, the system
can look at the graph afterwards and see whether the claim came true. This is
the one advantage this product has over every sentence-based todo list, and the
design leans on it everywhere.

**A human has to understand it before an agent uses it.** Agent behavior is out
of scope in this folder on purpose. Every screen and every rule here should
make sense to a person who has never read this document, because if a person
cannot follow a plan, then nobody can review an agent that follows it.
