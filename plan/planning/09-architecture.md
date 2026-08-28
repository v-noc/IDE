# 09 — Architecture

The previous files kept saying "this is derived". That is only a good idea if
deriving is fast. This file explains where the data lives, what is computed
when, and how a screen full of computed values is produced without asking the
database a hundred separate questions.

No code, and no final query shapes. What matters here is which pieces exist and
what each one is responsible for.

---

## 1. Where the data lives

Tasks are project data, so they live where the code graph, the documents, and
the conversations already live: in the project's own database, on the working
branch, read through the same scoped client everything else uses.

```
   PROJECT DATABASE, current branch
   ┌───────────────────────────────────────────────────────────┐
   │  code graph      folders · files · classes · functions ·  │
   │                  calls                                     │
   │                                                            │
   │  documents       written by the describe and document      │
   │                  tools                                     │
   │                                                            │
   │  work            tasks (with parent_id, document,          │
   │                  node links, events) ·                     │
   │                  conflict decisions                        │
   └───────────────────────────────────────────────────────────┘
```

Two consequences follow, and both are accepted deliberately.

**Work is committed with the code.** Every change to a task is a commit in the
same history as the code graph. The record of how a plan changed over time comes
free, which is why the planning model itself does not need to store history
beyond its events.

**Work is per branch.** An experiment on a branch has its own view of the work,
and promoting a branch merges the work along with everything else. If real use
shows that tasks should follow the project rather than the branch, the escape
is to read the work region through a second client pinned to one branch. The
model does not change either way, only the scoping does, so this is a seam
rather than a decision that has to be made now.

---

## 2. Two stored indexes, three logical lookups

Almost every derived value in this design comes from one of three lookups. They
are stored efficiently in two places: child tasks carry parent pointers, and
parent tasks carry link and dependency lists.

```
   ① CONTAINMENT (stored as parent_id on the child)
      stored     child ──parent_id──► task
      computed   task ──► its parents (at most one)
                 task ──► its depth and breadcrumb
                 task ──► its children (reverse of parent_id)

   ② LINKS AND DEPENDENCIES (stored on the task)
      stored     task ──► node_links[], each with a mode
                 task ──► depends_on[]

      computed   node ──► every task that links to it, with modes
                 task ──► effective links, including descendants
                 task ──► what it blocks (reverse of depends_on)
                 task ──► blocked or ready (from depends_on + links)
```

The pattern is the same: **store one direction, compute the other.** Storing
both directions would mean two copies of one fact, and two copies eventually
disagree.

Containment is now simpler than before: a task has exactly one parent, so there
is no deduplication needed when rolling up links or progress. A child task
queries its parent by its own parent_id field, and a parent queries its
children by scanning for tasks with its id in their parent_id.

The link index is the one that carries the product's most distinctive feature,
because it is what answers "who is about to touch this node" from anywhere in
the interface. It is keyed by node id for links that resolve, and by qualified
name for links that do not resolve yet, since a planned node has no id until it
exists.

---

## 3. Three storage categories, not two

It is tempting to treat everything as either stored or derived. That split is
too coarse, and the place it breaks is always the same: whole-project questions.

```
   ① STORED TRUTH
      Written by a person or an agent. The three edges plus the task fields.
      Never computed, never regenerated.

   ② REGENERABLE INDEX
      Materialized, single writer, rebuilt from stored truth, never hand-edited.
      Safe to persist, because it can always be thrown away and rebuilt.

   ③ COMPUTED ON READ
      Everything in the derived table. Never persisted anywhere.
```

The middle category is the one the original design was missing. The per-level
batching in section 5 works because a board level is a bounded set of tasks. The
whole-project queries — every contested node in the project, everything ready
anywhere — have no such bound, and they are the first thing to break at scale.

Those belong in category ②: a materialized index with a single writer, rebuilt
from stored truth whenever the parser runs or a link changes.

This preserves the discipline that matters — **no `is_blocked` column that rots
on a task** — while giving an escape hatch for the queries that genuinely cannot
be recomputed per request. The test for whether something may be materialized is
not "is it expensive" but **"can it be rebuilt from stored truth alone, by one
writer, without a human ever editing it"**.

---

## 4. One evaluation function

Every derived condition is computed by a single pure function.

```
   evaluate(task, snapshot) -> {
       blocked, waiting_on_code, ready, verified,
       contested, progress, blocked_below
   }
```

`snapshot` is an **explicit input**, not something the function fetches:

```
   snapshot = {
       dependency_statuses   status of every task in depends_on
       existing_nodes        node ids and qnames that exist in the graph now
       other_open_links      write-mode links held by other open tasks
       child_statuses        status of the task's direct children
   }
```

**No database access inside the function.** That single constraint is what makes
this work:

- The API, the UI payloads, the agent, and the tests all call the same function,
  so no two surfaces can drift into different answers about the same task.
- It can be snapshot-tested with no database at all. Every rule in
  [rules.md](rules.md) becomes a table of inputs and expected outputs.
- Batching stays a caller's concern. Section 5 assembles one snapshot for a
  whole screen, then calls `evaluate` once per task in memory.

This is the difference between a design that behaves like a rule engine and one
where the same logic is reimplemented slightly differently in six places.

---

## 5. One pass per screen, not one pass per card

The rule that keeps derivation affordable is that **derived values are computed
for a whole screen at once**, never per card.

When somebody opens a board level, the server does roughly this:

```
   1. Read the level's tasks
      the children of the current task (where parent_id = current_id), or tasks
      where parent_id is null for the root level.

   2. Collect every id that will be needed
      child task ids, dependency target ids, node ids from links.

   3. Ask three batched questions
      · which of these node ids still exist in the graph
      · what is the status of these dependency targets
      · what links do other open tasks have on these same nodes

   4. Compute everything in memory, in one pass
      blocked · waiting · ready · progress · rollups · contested ·
      verified

   5. Return one payload
```

A level with twelve cards costs a handful of queries, not thirty-six. This is
the same shape as the node work summary, which batches one existence check
across every node the board mentions — a pattern the codebase has already
proved at this scale.

---

## 6. The three summaries

Three computed payloads serve the entire product. Everything on screen reads
one of them, and nothing recomputes anything for itself.

```
   BOARD LEVEL SUMMARY
     for the tasks at one level: status, condition chips, progress,
     rollup counts, contested markers
     read by: the board, the list view, the task tree in the sidebar

   NODE WORK SUMMARY
     for a set of node ids: which tasks link to them, with modes,
     which are contested, which are sequenced by a dependency
     read by: canvas badges, node popovers, sidebar tree badges,
              the contested nodes list

   TASK DETAIL
     one task, fully expanded: document, links with their states, children
     with their conditions, dependencies both ways, conflicts, events
     read by: the detail panel
```

Keeping this to three payloads is what stops the interface from drifting into
a state where two panels show different answers to the same question. If a new
surface needs a computed value, it reads one of these three or the value is
added to one of them.

---

## 7. Rollup, without walking the tree every time

Rollup is the one genuinely expensive part of the recursive model. A parent
card wants to show the number of blocked tasks inside it and the union of every
descendant's links, and doing that naively means walking a subtree per card.

Three things keep it cheap.

**Rollups are computed for the level, not the card.** Opening a level loads the
subtree information for the cards on that level once, in a single traversal,
sharing everything.

**Depth is bounded in practice.** The guidance in [00](00-mental-model.md) puts
most trees at two or three levels. The system does not enforce that, so the
traversal has a depth ceiling with a visible marker when it is hit, rather than
silently producing a wrong count.

**The summary is cached per level and invalidated by events.** Any write that
could change it clears the relevant cache entry and emits an event that the
frontend uses to refetch.

```
   WRITES THAT INVALIDATE A LEVEL SUMMARY
     task created, deleted, status changed, moved
     parent changed, or a sibling reordered
     task soft-deleted or restored
     dependency added or removed
     node link added, removed, or changed
     conflict decision recorded
     a reparse changed the set of nodes
```

That last one is the interesting case, and it is worth being honest about it.

---

## 8. What happens when the parser runs

The parser rewrites the graph whenever files change. This can change the answer
to questions the work layer is asking, without anybody touching a task:

- a `create` link becomes fulfilled because the node now exists,
- a `affects` link becomes unresolved because the node was renamed,
- a task becomes verified because its last pending create landed.

None of this needs the parser to know that work exists, and that matters,
because the parser is complicated enough already. Since nothing is stored,
correctness is automatic; only freshness of the cache is at stake.

```
   TWO LEVELS OF FRESHNESS

   guaranteed correct   any read that misses the cache computes from the
                        current graph, so the answer is never wrong

   possibly stale       a cached summary can be up to one cache period
                        behind after a reparse
```

The clean fix is one event emitted at the end of the parser's commit batch,
which the work layer listens to and uses to clear affected entries. That is a
small hook and it belongs to whichever component owns the parser's batching. As
long as it is absent, badges correct themselves within a short window, which is
acceptable because nothing depends on the badge being instantaneous.

---

## 9. Answering the two lookups

**Task to nodes** is a walk down the `parent_id` index, collecting links, then
one batched existence check on the node ids gathered. One traversal, one query.
No deduplication is needed, because a task appears in the subtree exactly once.

**Node to tasks** is a direct read of the link index for that node id, followed
by a batched read of the tasks it names. Because the index is keyed by node id,
this is a single lookup regardless of how many tasks exist, which is what makes
it affordable to show a badge on every node on the canvas.

Planned nodes need one extra step. A link with no node id is indexed by its
qualified name instead, so a lookup on a node also checks whether anything is
planning to create something with that name. This is what surfaces the
duplicate-create warning before either node exists.

---

## 10. Scale, honestly

The realistic numbers for a project are a few hundred tasks, a few thousand
node links, and a graph with tens of thousands of nodes. At that size,
everything above is comfortable, and the deciding factor is the number of round
trips rather than the size of any single result.

Two things would change the picture, and both have a known answer that is not
built now:

**Thousands of tasks.** The level board already limits what is read to one
level, so the board stays fine. The part that would feel it is the contested
nodes list, and any other whole-project question. Those move from an in-memory
pass to a **regenerable index** — category ② in section 3, which exists exactly
for this.

**Very deep trees.** The depth ceiling protects the traversal, and the marker
tells the user that a count is partial rather than pretending it is complete.

---

## 11. What is deliberately not built

**No stored derived state.** No `is_blocked` column, no cached progress count,
no conflict table. Every one of these would be wrong within minutes of being
written, and a wrong stored value is undetectable while a slow computation is
merely slow.

**No live collaboration.** Two people editing one task document at the same
time is out of scope. The existing socket events tell the other side to refetch,
and last write wins, which matches how the rest of the product behaves today.

**No separate search index.** Finding tasks by text uses whatever the project
already uses. Nothing in this design depends on search.

**No agent-specific storage.** An agent that proposes a plan writes exactly
the same records a person writes, with `created_by` naming the run. The reasons
for that choice are in [12 — Agent seams](12-agent-seams.md).

The next file, [10 — API surface](10-api-surface.md), lists the operations this
architecture has to support, described in plain language rather than as
endpoints.
