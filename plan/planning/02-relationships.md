# 02 — Relationships

A relationship type is not free. Every one you add is a question the user has
to answer correctly for as long as the product exists, and if two relationship
types can be confused with each other, the database quietly fills with data
that means nothing. Queries built on that data then produce confident wrong
answers, which is worse than having no data at all.

So this file works through every relationship the planning system could
plausibly have, and keeps only the ones that earn their place. The test each
one has to pass is the same:

> **Does this relationship record something that cannot be worked out from what
> is already stored, and does it change a decision somebody makes?**

If it can be computed, it should be computed. If it does not change anybody's
behaviour, it should not exist.

---

## The candidates

These are the relationship types that came up while designing this, including
the obvious ones from other task tools.

```
   between work and work            between work and code
   ─────────────────────            ─────────────────────
   contains  (parent/child)         context
   depends_on                       affects
   blocked_by                       references
   related_to                       anchor
   duplicates
   delegates
```

Ten candidates. Here is what happens to each of them.

---

## Kept: contains, as an ordered list on a version

**What it is.** A version holds an ordered list of references to child tasks.
This is how a task becomes part of another task.

**Why it is stored.** It cannot be derived from anything. Somebody decided that
"Comment model" is part of "Add comments", and that decision is the structure
of the work.

**Why it lives on the version rather than on the task.** Because the breakdown
*is* part of the approach. Two different approaches to the same promise have
different steps, and if the child list lived on the task there would be nowhere
to put the second breakdown.

**Why it is a reference rather than ownership.** This is the property the whole
design rests on. Because the version only points at children, you can rewrite
an approach, replace it, or abandon it, and every child task continues to exist
with its own status and history. Nothing has to be rescued, copied, or
reattached.

```
   VERSION 1 of "Add comments"          VERSION 2 of "Add comments"
     1 ─► VN-8   Comment model            1 ─► VN-15  Add comments list to Post
     2 ─► VN-9   Comment write path       2 ─► VN-12  Show comments on page
     3 ─► VN-12  Show comments on page         ▲
             ▲                                 │
             └─────────  the same task  ───────┘
                         referenced by both
```

**The direction it is stored in.** The reference lives on the parent's version,
pointing down. The child holds nothing. This is deliberate: a child can be
referenced by several parents, so storing a single parent field on the child
would either be a lie or would forbid sharing. "Who are this task's parents?"
is answered by an index, described in [09](09-architecture.md).

**Tradeoff.** Storing the edge only downward means finding a task's parents
costs a lookup instead of reading a field. In exchange, shared work is
representable, and there is exactly one copy of the truth rather than a
parent field and a children list that can disagree.

---

## Kept: depends_on, between two tasks

**What it is.** One task cannot be finished until another task is finished.

**Why it is stored.** Some ordering has no trace in the code at all. "Do not
start the filtering work until moderation ships, because we only want to
maintain one of them at a time" is a decision, not a fact about functions.
Nothing can derive it.

**Why it connects tasks and only tasks.** Every piece of work in this system is
a task, so the edge can be as precise as the real reason. If the truth is "I
need that one function", the edge points at the small task that writes that
function, not at the large task that contains it.

```
   VN-9   Comment write path  ──depends_on──►  VN-5   Write current_user()
     child of VN-3 Comments                      child of VN-1 Authentication
```

**The one guard.** A task may never depend on its own ancestor or its own
descendant.

```
   REFUSED                              WHY
   ───────                              ───
   VN-3  ──contains──►  VN-11           VN-3 is not finished until VN-11 is
   VN-11 ──depends_on─► VN-3            VN-11 cannot start until VN-3 is

                                        Neither can ever finish.
```

Containment already expresses "this is part of that". Ordering inside a family
is expressed by the child list order and by dependencies between siblings, and
never by an edge that points back up the tree.

**Tradeoff.** Allowing dependencies at any depth means the dependency graph can
become large and cross-cutting, and a person looking at a high-level card may
not immediately see that something four levels down is blocked. The design pays
for this by rolling blocking status up the tree, so a parent card shows that
something inside it is stuck, with a link to the exact task.

---

## Cut: blocked_by, as a separate edge

**Why it was proposed.** Most task tools have both "depends on" and "blocked
by", and they feel different when you say them out loud.

**Why it is cut.** They are the same edge read from opposite ends. If A depends
on B, then B blocks A. Storing both means storing the same fact twice, and two
copies of one fact will eventually disagree.

More importantly, being *blocked* is a state rather than a relationship. A task
is blocked when something it depends on is unfinished, and that can be computed
in the moment it is asked.

```
   STORED       VN-9 ──depends_on──► VN-5
   DERIVED      VN-9 is blocked, because VN-5 is not done
   DERIVED      VN-5 blocks VN-9      ← the reverse view, computed
```

The current system already has a field called `blocked_by`. Keeping that field
name is fine; what matters is that it means "depends on" and that there is only
one of it. This is covered in [15 — Migration](15-migration-from-today.md).

---

## Cut: related_to

**Why it was proposed.** It is comforting. Two pieces of work feel connected
and there is a button to say so.

**Why it is cut.** It fails both halves of the test. It cannot be acted on,
because nobody knows what to do differently when two things are "related", and
in this product it is very nearly derivable already.

Relatedness between two tasks almost always means one of three things, and each
of them is better expressed by something the system already has.

```
   "these two are related" usually means …

   … they touch the same code    ──►  already visible. Both link to the same
                                      node, and the node lists both.

   … one must come first         ──►  that is depends_on. Say it properly.

   … they are part of one theme  ──►  that is a parent task, or a label.
```

**Tradeoff.** Somebody will occasionally want to connect two tasks that share
no code, no ordering, and no parent. For that rare case, a sentence in the
document mentioning the other task's key is enough, and a mention can be turned
into a clickable link without adding a relationship type to the model.

---

## Cut: references, merged into context

**Why it was proposed.** "This task references that class" sounds different
from "this class is context for the task".

**Why it is cut.** They are the same thing said twice. Both mean: to do this
work you need to look at that code, and you are not going to change it. One
mode, called `read`, covers it, and the interface labels the list **Context**
because that is the word people use.

Having both would immediately create the question "should I put this under
references or under context?", which is exactly the kind of unanswerable
question that fills a database with noise.

---

## Kept, as modes rather than as separate relationship types: context and affects

**What they are.** A version points at graph nodes, and every pointer carries a
mode.

**Why they are one mechanism and not two.** Because the most valuable question
in the whole system is asked from the code side, not from the work side.

```
   Standing on  function createComment()  and asking:
   "who is about to touch this?"

   ONE MECHANISM                          TWO MECHANISMS
   ─────────────                          ──────────────
   read the links on this node,           read the affects table,
   group them by mode.                    then read the context table,
                                          then merge them, forever,
   VN-11  modify   ← a collision          in every query, in every
   VN-30  modify   ← a collision          screen, and hope nobody
   VN-40  read     ← worth knowing        forgets one of them.
```

One list with a mode column answers it in a single pass. Two separate
relationship types answer it in two passes that have to be kept in step in
every place the question is asked.

**Why the modes are exactly these five.** `about` is the vague one, used by
anchors, and it never triggers collision warnings. `read` means look but do not
change. `create`, `modify`, and `delete` are the three things you can do to a
node, and they are distinguished because they behave differently: two `create`
links on the same name are a duplicate, a `delete` under somebody else's
`modify` is severe, and a `create` is the one mode that is allowed to point at
a node that does not exist yet.

**Tradeoff.** Five modes is more than one, and people will sometimes choose the
wrong one. The design accepts this because a wrong mode is detectable. After the
work lands, the commits say which nodes actually changed, and the system can
point out that a task marked something `read` and then rewrote it. A mistake
that can be noticed is much better than a missing distinction that cannot be
recovered.

---

## Kept: anchor, as the `about` mode on the task

**What it is.** A soft pointer saying roughly where in the code this work
lives.

**Why it stays even though `read` and `modify` exist.** Anchors are written
early, when nobody knows the verbs yet. Somebody right-clicks a file on the
canvas and says "new task here". At that moment the honest statement is "this
work is around here", and forcing a choice between `read` and `modify` would
make people guess and then be wrong.

Anchors also live on the **task** rather than on a version, because where work
lives does not change when the approach changes. A version can come and go, and
the anchor stays.

**Tradeoff.** There are now two places a task points at code, which needs
explaining once. The distinction is stable enough to be worth it: *the anchor
is where the work lives, the links are what an approach will do.*

---

## Cut: duplicates

**Why it was proposed.** People file the same work twice, and every tracker has
a way to mark that.

**Why it is cut.** Marking a duplicate is a housekeeping action, not a
relationship worth modelling. In this system the natural resolution is simply
to merge: point the surviving task's version at whatever children the duplicate
had, copy anything useful out of its document, and delete the duplicate with a
note saying it was merged into VN-9.

If it later turns out that people need to find the old key after a merge, the
cheapest answer is a redirect entry from an old key to a new one, which is a
lookup table rather than a relationship in the work model.

---

## Cut: delegates

**Why it was proposed.** When a step turns out to be big, it feels like the
step should stay where it is and point at the bigger piece of work that took it
over.

**Why it is cut.** In a model where everything is a task, there is nothing to
delegate. The step already is a task. If it grows, you give it children. If it
belongs under a different parent, you move the reference. No third thing is
needed to connect a small work object to a large one, because there is only one
kind of work object.

---

## The two laws that came out of this

Two general rules emerged while making these cuts, and they are worth stating
on their own because they will settle future arguments too.

### Law 1 — Point hard references at durable things only

Anything a person can throw away must not be the target of a stored reference.

```
   DURABLE                       FRAGILE
   ───────                       ───────
   a task                        a version's list of steps
   a graph node id + name        a graph node id on its own
```

Tasks are durable, so dependencies point at tasks. Graph nodes are fragile,
because the parser deletes and recreates them whenever a file changes, so every
pointer into the graph is stored as a soft id **plus a snapshot of the name and
kind**. When the node disappears, the pointer becomes a visible warning that
still reads sensibly, instead of a broken reference nobody can interpret.

### Law 2 — One fact, one place

If a fact is stored twice, the two copies will disagree, and no amount of
careful code prevents it forever. So:

- `depends_on` is stored once, in one direction, and the reverse view is
  computed.
- Containment is stored once, on the parent's version, and parenthood is
  computed.
- A collision between two tasks is not stored at all, only the human decision
  about it.
- Progress, blocking, readiness, and contested nodes are never stored.

---

## The final catalog

```
   STORED RELATIONSHIPS  (there are three)
   ───────────────────────────────────────
   version ──ordered list of references──► task        containment
   task    ──depends_on───────────────────► task        ordering
   version ──link with a mode─────────────► graph node  code involvement
   task    ──anchor (mode: about)─────────► graph node  where the work lives

   DERIVED, ON EVERY READ
   ──────────────────────
   parents of a task              from the containment index
   blocks (the reverse view)      from depends_on
   blocked / ready                from depends_on plus link states
   progress                       from the active version's children
   effective links of a parent    from the union of its descendants' links
   contested nodes                from write-mode links on the same node
   orphaned / shared              from how many active versions refer to a task
```

Four stored arrows. Everything else the product shows is computed from them.

The next file, [03 — Data model](03-data-model.md), turns this into concrete
fields, and marks clearly which ones are written and which ones are calculated.
