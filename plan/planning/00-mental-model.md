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
   │  anchors       Roughly where this work lives in the codebase.         │
   │                                                                       │
   │  context       The nodes somebody must read to do this work, but will │
   │                not change. Optional.                                  │
   │                                                                       │
   │  affects       The nodes this work will create, change, or delete.    │
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
        ├── read ────────►  class Post
        ├── read ────────►  function current_user()
        ├── create ──────►  function createComment()
        └── modify ──────►  class Comment
```

The modes that only read become the **Context** list when the task is displayed,
and the modes that write become the **Affects** list. Underneath they are the
same mechanism, which is what allows a single question to be asked from the
other direction: *given this function, which tasks are about to touch it, and
are any of them going to change it?*

There is one rule about the code side that never bends anywhere in this design.

> **The graph has exactly five node kinds, which are folder, file, class,
> function, and call. A field is not a node. A column is not a node. A parameter
> is not a node. An endpoint is not a node.**

When a piece of work is about a field, it links to the class or function that
contains the field, and the field is described in the task's own words. So a
task titled "Add an `author_id` field to Comment" links to the class `Comment`
with mode `modify`, and the sentence carries the detail. This keeps the
planning layer honest about what the parser really produces, and it means no
task can ever point at a node kind that does not exist.

---

## 4. Why a task can have more than one version

Sometimes there is more than one sensible way to do something, and the choice
between them is the most valuable thinking in the whole task. That thinking
needs somewhere to live, and it needs to survive after the choice is made, so
that six months later somebody can see not only what was built but what was
considered and rejected.

A **version** is one answer to the question "how are we going to do this?".

```
   TASK  "Add comments"
     │
     ├── version 1   "Separate Comment class"          ★ ACTIVE
     │      document   the long write-up of this approach
     │      context    class Post · class User
     │      affects    create class Comment
     │                 create function createComment()
     │      children   1 ─► TASK "Comment model"
     │                 2 ─► TASK "Comment write path"
     │                 3 ─► TASK "Comment read path"
     │                 4 ─► TASK "Comment moderation"
     │                 5 ─► TASK "Show comments on the post page"
     │
     └── version 2   "Store comments inside the Post document"   draft
            document   a different write-up, with its own reasoning
            affects    modify class Post
            children   1 ─► TASK "Add a comments list to Post"
                       2 ─► TASK "Show comments on the post page"   ◄─ same task
```

Two things about that picture matter more than anything else in this document.

**A version refers to its children. It does not own them.** The tasks in the
list exist in their own right. They have their own identity, their own status,
their own history, and their own place on the board. A version is a curated,
ordered list of pointers to them.

**The same child can appear in more than one version.** "Show comments on the
post page" is needed either way, so both versions point at the same task. If it
was already finished under version 1, it is still finished under version 2,
automatically, because it is the same task and nothing was copied.

Together these two facts mean that switching approach is a cheap, safe, and
ordinary thing to do. Activate version 2 and nothing is deleted. "Comment
moderation" is still a task with whatever status it had, it simply is not
referred to by the active version any more, which the interface can show as a
quiet note on the card rather than as a disappearance.

### Only some fields belong to a version

A version exists to describe an approach, so only the fields that genuinely
differ between two approaches belong to it. Everything that describes what the
work *is*, rather than how it will be done, belongs to the task and is shared
by every version.

| Field | Belongs to | Reason |
|---|---|---|
| key, title, description | Task | "Add comments" is the same promise whichever approach wins |
| type, priority, labels, status | Task | The board's view of the work does not change because the method changed |
| anchors | Task | Roughly where the work lives is stable across approaches |
| depends_on | Task | Whether authentication must land first is a fact about the promise |
| **document** | Version | The write-up of the approach is the approach |
| **context nodes** | Version | Different approaches read different code |
| **affected nodes** | Version | Different approaches change different code |
| **ordered children** | Version | Different approaches have different steps |

In everyday use you never think about versions, because **every task is created
with exactly one version and that version is active**. While there is only one,
the interface shows the document, the context list, the affects list, and the
children as if they were plain fields on the task, and the word "version" is
not shown anywhere. A second version appears only when somebody deliberately
asks for an alternative, which is rare and always intentional.

The tradeoff is worth naming plainly. The cost is one extra layer of
indirection in the data model, and the cost of explaining that layer to
somebody who eventually meets it. The benefit is that alternatives, revisions,
and abandoned approaches are all supported by the same mechanism, with no
second entity type and no rules for rescuing orphaned work.

---

## 5. The board shows one level at a time

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

## 6. How deep the tree should go

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

The version on the right is not more precise. It is the same information spread
across five cards, and each of those cards now needs a status, a position, and
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

## 7. Dependencies point at tasks, at any depth

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
rewritten, moved to a different parent, or given a second version, and the
dependency still means what it meant, because it points at the work itself
rather than at somebody's current description of the work.

Three rules keep this from becoming a tangle, and each is developed properly in
[06 — Dependencies and readiness](06-dependencies-and-readiness.md).

**A dependency may never connect a task to its own ancestor or descendant.**
Containment already describes that relationship. Adding a dependency on top of
it creates a deadlock in which the parent waits for the child while the child
waits for the parent, so the system refuses the edge and explains why.

**Position in a list never blocks anything.** A version's children are written
in a sensible reading order, and that order is genuine advice about where to
start. It is not a constraint. Two children that need nothing from each other
can be worked on at the same time, and the system works that out from the
actual dependencies rather than from the numbering.

**Most dependencies should be suggested rather than typed.** Because every task
names the nodes it needs and the nodes it will create, the system can notice
that one task is waiting for a function another task is about to write, and
offer the dependency instead of hoping a human remembers it.

---

## 8. Two tasks touching the same code

Once tasks name the nodes they affect, a question that no ordinary task board
can answer becomes easy: *is anybody else about to touch this?*

```
   function createComment()
        ▲                    ▲
        │ modify             │ modify
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

## 9. What this shape costs

It would be dishonest to present the recursive model as free. Three costs come
with it, and none of them can be removed completely. They can only be managed.

**Counting becomes ambiguous.** In a flat system, "eleven open tasks" means one
thing. In a tree, eleven could be the roots, or the leaves, or everything. Every
count, progress bar, and report has to say which depth it is talking about. The
level board helps, because a count on screen is always a count of what is
currently visible, but the ambiguity never disappears entirely.

**Nothing structurally prevents a badly shaped tree.** There is no floor. A
person can keep breaking work down until every line of code has a card. Section
6 is the defence, and it is guidance rather than enforcement, which means the
interface has to keep nudging rather than blocking.

**Versions can appear at any depth.** A task three levels down can have two
versions of its own. That is powerful, and it is confusing if the interface
does not constantly show which version of which task you are looking at. The
breadcrumb has to carry that information, and the design in
[11 — UI surfaces](11-ui-surfaces.md) treats it as a requirement rather than a
nicety.

Against those costs, one entity type means one set of rules to learn, one place
where dependencies live, one shape of query, one board, and one detail panel.
Work can grow or shrink without being converted into something else, and
changing your mind about an approach never destroys anything. That is the trade
this design makes deliberately.

---

## 10. The whole model on one screen

```
                     ┌───────────────────────────────────────────────┐
   THE BOARD  ────►  │  TASK                                         │
   SHOWS ONE         │  key · title · description · type · status    │
   LEVEL OF          │  priority · labels · anchors · depends_on     │
   THESE             │  notes                                        │
                     └────────────────┬──────────────────────────────┘
                                      │ has one or more versions,
                                      │ exactly one of them active
                     ┌────────────────▼──────────────────────────────┐
                     │  VERSION   (invisible while there is only one) │
                     │  document · context nodes · affected nodes    │
                     │  ordered list of child task references        │
                     └───────┬────────────────────────┬──────────────┘
                             │                        │
                             │ children               │ links, each with a mode
                             ▼                        ▼
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
```

Two stored relationships hold the whole system together. A version refers to
child tasks in order, and a task depends on another task. Everything else that
the product needs to know — whether something is blocked, whether a node is
contested, how much of a tree is finished, which work touches a given function
— is computed from those two relationships plus the links into the graph.

The next file, [01 — Concepts](01-concepts.md), defines each term precisely,
including what each one is deliberately not.
