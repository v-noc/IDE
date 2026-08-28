# 00 — The Mental Model

This file explains the idea behind the planning system in plain language,
before any field names, screens, or storage decisions appear. Everything in the
later files is a consequence of what is described here, so it is worth reading
slowly even though it contains almost no technical detail.

---

## 1. What a task is

A task is a promise that something will become true, together with everything
somebody needs in order to make it true.

That second half matters. In most tools a task is a single line of text with a
checkbox next to it, and all of the real thinking happens somewhere else, in a
document, in a chat thread, or in somebody's head. Here the task is the place
where the thinking lives.

```
   ┌─ TASK  VN-9  "Comment write path" ───────────────────────────────────┐
   │                                                                       │
   │  title         Comment write path                                     │
   │                                                                       │
   │  description   One short paragraph saying what this work is and why   │
   │                it matters. This is what a board card shows.           │
   │                                                                       │
   │  document      The long write-up. The approach, the reasoning behind  │
   │                it, what was considered and rejected, the shape of the │
   │                code, anything a reader needs to actually do the work. │
   │                                                                       │
   │  context       The nodes somebody must read to do this work, but will │
   │                not change. Optional.                                  │
   │                                                                       │
   │  affects       The nodes this work will create, change, or delete.    │
   │                                                                       │
   │                Where the work lives is not a field. It is derived     │
   │                from the nodes above.                                  │
   │                                                                       │
   │  children      An ordered list of smaller tasks, if it has any.       │
   │                                                                       │
   │  depends_on    Other tasks that have to finish before this one can.   │
   │                                                                       │
   │  status        Which column of the board it sits in.                  │
   └───────────────────────────────────────────────────────────────────────┘
```

The description and the document have different jobs and both are needed. The
description is for somebody scanning a board who wants to know in two seconds
whether this card is the one they are looking for. The document is for somebody
who has decided to do the work and now needs the detail. Forcing both jobs into
one field always ends badly, because a description long enough to be useful is
too long to scan, and a description short enough to scan is too thin to work
from.

---

## 2. Why work is recursive

Real work does not come in two neat sizes. Sometimes "add comments" is one
afternoon of typing, and sometimes it is three weeks of design with six people
involved. A system that decides in advance that there are exactly two levels,
a big level and a small level, will be wrong constantly, and people will spend
their time arguing about which level something belongs to instead of doing it.

So there is only one kind of work object, and it contains itself.

```
   TASK  "Add comments"
     ├── TASK  "Comment model"
     │     └── TASK  "Add author_id and post_id fields to Comment"
     ├── TASK  "Comment write path"
     ├── TASK  "Comment read path"
     ├── TASK  "Comment moderation"
     │     ├── TASK  "Detect banned words"
     │     └── TASK  "Hide a comment from the post page"
     └── TASK  "Show comments on the post page"
```

Every box in that picture is the same kind of thing. Each one can have a
description, a document, context nodes, affected nodes, dependencies, a status,
and children of its own. Nothing is a second-class citizen, and nothing has to
be converted into a different type when it turns out to be bigger or smaller
than expected.

The word *subtask* is still useful when talking to people, but it does not name
a type. A subtask is just a task that some other task refers to as a child. If
a piece of work grows, you add children to it. If it turns out to be small, you
delete its children. If it belongs somewhere else, you move it. None of those
actions require converting anything into anything.

### This matches the shape of the codebase

The code graph in this product is already recursive. A folder holds files, a
file holds classes, a class holds functions, and a function holds calls. The
work tree now has the same shape, which means the same navigation, the same
breadcrumbs, the same idea of opening one level at a time, and the same style
of query serve both trees.

```
   CODE TREE                          WORK TREE
   ─────────                          ─────────
   folder  app/                       task    Add comments
     file    models.py                  task    Comment model
       class   Post                       task    Add author_id field
         function  createPost()         task    Comment write path
           call    save()                 task    Write createComment()
```

That symmetry is not decoration. It means a person who has learned to move
around the code canvas has already learned to move around the work.

---

## 3. Where the code fits in

Every task can point at nodes in the code graph, and each pointer carries a
**mode** that says what the work does to that node.

```
   TASK "Comment write path"
        │
        ├── read ───────►  class Post
        ├── read ───────►  function current_user()
        ├── create ─────►  function createComment()
        └── affects ────►  class Comment
```

There are four modes — `read`, `create`, `affects`, `delete` — and no vague one.
The modes that only read become the **Context** list when the task is displayed,
and the modes that write become the **Affects** list. Underneath they are the
same mechanism, which is what allows a single question to be asked from the
other direction: *given this function, which tasks are about to touch it, and
are any of them going to change it?*

Because there is no vague mode, **every link makes a claim the graph can check**.
That is the whole reason for putting work on top of a graph, and it is why an
earlier "this work is around here somewhere" pointer was removed rather than
kept for convenience.

It also means the task never says where it lives. That question is answered by
looking at the links: the nearest container holding all of them, shown when it
is specific enough to be useful.

There is one rule about the code side that never bends anywhere in this design.

> **The graph has exactly five node kinds, which are folder, file, class,
> function, and call. A field is not a node. A column is not a node. A parameter
> is not a node. An endpoint is not a node.**

When a piece of work is about a field, it links to the class or function that
contains the field, and the field is described in the task's own words. So a
task titled "Add an `author_id` field to Comment" links to the class `Comment`
with mode `affects`, and the sentence carries the detail. This keeps the
planning layer honest about what the parser really produces, and it means no
task can ever point at a node kind that does not exist.

---

## 4. The board shows one level at a time

A recursive tree could easily produce a board with two hundred cards on it,
which would be useless. The board avoids that by behaving like a file explorer:
it shows the children of one task, and you move up and down.

```
   BOARD AT THE ROOT                     BOARD INSIDE "Comments"
   ┌───────┬─────────┬───────┐           ▸ Comments ▸
   │ todo  │ doing   │ done  │           ┌──────────┬──────────┬────────┐
   ├───────┼─────────┼───────┤           │ todo     │ doing    │ done   │
   │ VN-3  │ VN-1    │ VN-2  │  click    ├──────────┼──────────┼────────┤
   │ Comm… │ Auth    │ Posts │  VN-3 ──► │ VN-10    │ VN-9     │ VN-8   │
   │ 1/5   │ 2/3     │       │           │ read     │ write    │ model  │
   └───────┴─────────┴───────┘           │ VN-11    │          │        │
                                          │ moderat… │          │        │
                                          └──────────┴──────────┴────────┘
```

You start at the root and see a handful of cards, which is an honest summary of
the whole project. You open one and the board becomes that task's children. A
breadcrumb takes you back up. If you are going to work inside one area for a
week, you pin that level as your board root and the rest of the tree stops
distracting you.

Detail never floods the board, because detail is always one level down instead
of on the same screen. This is the thing that makes a recursive model practical
rather than overwhelming, and it is why the level board is treated as part of
the model rather than as a later interface decision.

---

## 5. How deep the tree should go

Nothing in the model stops somebody from building a tree six levels deep, so
guidance has to do that work instead of a rule. A rule would be wrong anyway,
because occasionally a piece of work really is that deep.

> **Stop breaking work down when a task describes one coherent change that you
> could explain to a colleague in a single sentence.**

Below that line, detail belongs in the task's document rather than in more
tasks.

```
   GOOD                                     TOO FAR
   ────                                     ───────
   VN-9  Comment write path                 VN-9   Comment write path
     VN-20  Write createComment()             VN-20  Import the Comment class
     VN-21  Validate that the post exists     VN-21  Add the function signature
                                              VN-22  Add the docstring
                                              VN-23  Add the post lookup line
                                              VN-24  Add the save call
```

The breakdown on the right is not more precise. It is the same information
spread across five cards, and each of those cards now needs a status, a position, and
possibly a dependency of its own. All of that belongs in the document of VN-20,
where it reads as one paragraph and costs nothing to maintain.

Two rules of thumb make this concrete in practice. Most trees are two or three
levels deep. Most levels hold between three and ten children. A level with
thirty children usually means the level above it was missing a grouping step,
and a level with a single child usually means that child should not exist.

The rule about node kinds from section 3 also limits depth naturally. Fields,
columns, parameters, and imports are never tasks, so "add the author_id field
to Comment" is a perfectly good leaf, and there is nothing underneath it to
break down.

---

## 6. Dependencies point at tasks, at any depth

Work often has to happen in a certain order, and the reason is usually
specific. It is rarely "all of authentication must be finished". It is usually
"I need the one function that tells me who the current user is".

Because everything is a task, a dependency can be exactly as precise as the
real reason, and it always points at something durable.

```
   VN-9  "Comment write path"  ──depends_on──►  VN-5  "Write current_user()"
     a child of VN-3 Comments                      a child of VN-1 Authentication
```

Both ends are real tasks with their own identity and status. Either side can be
rewritten, moved to a different parent, or broken into children, and the
dependency still means what it meant, because it points at the work itself
rather than at somebody's current description of the work.

Three rules keep this from becoming a tangle, and each is developed properly in
[06 — Dependencies and readiness](06-dependencies-and-readiness.md).

**A dependency may never connect a task to its own ancestor or descendant.**
Containment already describes that relationship. Adding a dependency on top of
it creates a deadlock in which the parent waits for the child while the child
waits for the parent, so the system refuses the edge and explains why.

**Position in a list never blocks anything.** A task's children are ordered in
a sensible reading order, and that order is genuine advice about where to
start. It is not a constraint. Two children that need nothing from each other
can be worked on at the same time, and the system works that out from the
actual dependencies rather than from the numbering.

**Most dependencies should be suggested rather than typed.** Because every task
names the nodes it needs and the nodes it will create, the system can notice
that one task is waiting for a function another task is about to write, and
offer the dependency instead of hoping a human remembers it.

---

## 7. Two tasks touching the same code

Once tasks name the nodes they affect, a question that no ordinary task board
can answer becomes easy: *is anybody else about to touch this?*

```
   function createComment()
        ▲                    ▲
        │ affects             │ affects
        │                    │
   VN-11 "Moderation"    VN-30 "Rate limiting"        ← both plan to change it
```

The system does not have to guess. It reads the links, sees two pieces of open
work with write modes on the same node, and says so on the node, on both cards,
and in a list of contested nodes. If one of them is only reading, that is a
weaker signal and it is shown differently, because reading code somebody else
is rewriting is worth knowing about but is not a collision.

This is developed in [08 — Conflicts and concurrency](08-conflicts-and-concurrency.md).
The important idea for now is that the collision is **computed, never stored**.
What gets stored is only the human decision about it, such as "we discussed
this and it is fine", so that the record of what people agreed never gets mixed
up with the record of what the code actually says.

---

## 8. What this shape costs

It would be dishonest to present the recursive model as free. Two costs come
with it, and neither can be removed completely. They can only be managed.

**Counting becomes ambiguous.** In a flat system, "eleven open tasks" means one
thing. In a tree, eleven could be the roots, or the leaves, or everything. Every
count, progress bar, and report has to say which depth it is talking about. The
level board helps, because a count on screen is always a count of what is
currently visible, but the ambiguity never disappears entirely.

**Nothing structurally prevents a badly shaped tree.** There is no floor. A
person can keep breaking work down until every line of code has a card. Section
5 is the defence, and it is guidance rather than enforcement, which means the
interface has to keep nudging rather than blocking.

Against those costs, one entity type with a single parent means one set of rules
to learn, one place where dependencies live, one simple tree structure, and one
shape of query. Work can grow or shrink without being converted into something
else. Changing your mind about the approach does not require choosing between
versions; it means moving tasks around and updating the plan in the document.
That is the trade this design makes deliberately.

---

## 9. The whole model on one screen

```
                     ┌───────────────────────────────────────────────┐
   THE BOARD  ────►  │  TASK                                         │
   SHOWS ONE         │  key · title · description · type · status    │
   LEVEL OF          │  priority · labels · rank · events            │
   THESE             │  document                                     │
                     │  parent_id ─┐   position                      │
                     └──────┬──────┼───────────────┬─────────────────┘
                            │      │               │
                            │      │ points UP at  │ links, each with a mode
                            │      │ one parent    │ read·create·affects·delete
                            │      │               │
              children:     │      └──────────►    │
              the reverse   │        one TASK      │
              of parent_id  ▼                      ▼
                     ┌────────────────┐   ┌───────────────────────────┐
                     │  TASK          │   │  GRAPH NODE               │
                     │  (recursion)   │   │  folder · file · class ·  │
                     └────────────────┘   │  function · call          │
                                          │                           │
                                          │  a field is not a node.   │
                                          │  it is a sentence on the  │
                                          │  task, linked to the class│
                                          │  or function holding it.  │
                                          └───────────────────────────┘

              plus one more edge, task to task:   depends_on
```

Three stored edges hold the whole system together. A child points up at its one
parent, a task depends on another task, and a task links to a graph node with a
mode. Everything else the product needs to know — whether something is blocked,
whether a node is contested, how much of a tree is finished, which work touches
a given function — is computed from those three.

The next file, [01 — Concepts](01-concepts.md), defines each term precisely,
including what each one is deliberately not.
