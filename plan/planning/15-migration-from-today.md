# 15 — Growing From What Exists Today

The current system is not thrown away. Most of it is already the right shape,
and the parts that change do so by addition rather than by replacement. This
file says exactly what stays, what moves, what is added, and in what order it
could be built.

No code and no schema statements. What matters here is which existing ideas map
onto which new ones, and where the sharp edges are.

---

## 1. What exists now

The shipped system has a board with configurable columns, tasks with human keys,
subtasks stored as real task-to-task links, dependency links, soft anchors into
the code graph with name snapshots, a notes list used for history, and a summary
that computes which nodes are "hot" because two or more open tasks anchor to
them.

```
   TASK today
     key · title · description · type · status · priority · labels · rank
     subtasks    ──► other tasks       a set, unordered
     blocked_by  ──► other tasks
     anchors     ──► graph nodes       soft id + name snapshot
     notes
```

Three decisions already made there are load bearing, and this design keeps all
three.

**Subtasks are tasks.** They are stored as links from a task to other tasks,
not as a separate type. The recursive model is a continuation of that decision,
not a reversal of it.

**Anchors are soft.** A node id plus a snapshot of the name and kind, so a
deleted node produces a readable warning rather than a broken record. Every new
link in this design follows the same rule.

**Hotness is computed.** Nothing stores whether a node is contested. The whole
derivation discipline in this design is the same idea applied more widely.

---

## 2. What maps onto what

| Today | In this design | What changes |
|---|---|---|
| Task | Task | Gains versions and an active version pointer |
| Subtask set | Ordered child list on a version | Gains order and a home inside an approach |
| `blocked_by` | `depends_on` | Same edge, clearer name, plus two guards |
| Anchors | Anchors, mode `about` | Unchanged |
| Notes | Notes | Unchanged, with a few more system sentences |
| Board and columns | Board and columns | Unchanged, plus a level in the interface |
| Hot node summary | Node work summary | Extended with modes; the old rule still applies when no links exist |
| — | Version | New |
| — | Document | New |
| — | Node links with modes | New |
| — | Conflict decisions | New |

The important line in that table is the second one. Today a task holds a set of
subtasks. In this design the children live on the version, and they are ordered.

---

## 3. The one migration that has to happen

Every existing task needs a version, because the model says a task always has
exactly one active version.

```
   FOR EACH EXISTING TASK
     create version 1
       name        "Original"
       document    empty, or seeded from the description
       children    the existing subtask set, ordered by the children's
                   current rank so the order is stable and sensible
       links       none
     make it active
```

Everything else is left alone. Anchors stay on the task, dependencies stay on
the task, notes stay on the task, status and rank are untouched.

**Ordering is a guess, and it should be a visible one.** The existing subtask
set has no order, so ordering by rank produces something reasonable rather than
something meaningful. A note on each migrated version saying "order was
inherited from the board and may need review" is honest and costs nothing.

**Nothing is lost.** No existing field is dropped in this step. A task that
nobody ever opens again behaves exactly as it does today, because a task with
one empty version and a child list is what it already was.

---

## 4. What is deliberately not touched

**The parser, and every graph schema.** No node type gains a field pointing at
tasks. "Which tasks touch this node" stays a question asked from the work side,
using the link index, exactly as "which tasks anchor here" is answered today.
This keeps the parser, the group service, and every existing write path
untouched.

**Hard links between tasks.** Task to task references stay real links, which is
what gives referential integrity for children and dependencies.

**Soft links into the graph.** Node links join anchors in being stored as an id
plus a snapshot. A hard link would either block the parser's deletes or break.

**The board.** Columns, their flags, drag and drop, ranks, and the backlog rule
all stay as they are. The level is a view concept layered on top.

---

## 5. A sensible build order

Each phase is useful on its own, which matters because it means the work can
stop at any point without leaving something half-built.

### Phase 1 — versions and documents

Add versions, with the migration above. Add the document. Order the child list
and let it be dragged. Show the version switcher only when a task has more than
one.

**What this alone gives:** a real place to write down how work will be done,
alternatives that can be compared, and ordered steps. Nothing about the graph
has changed yet.

### Phase 2 — node links and modes

Add links with modes to versions. Extend the existing anchor summary into the
node work summary, keeping the current hot rule for tasks that have anchors but
no links, so nothing regresses while links are gradually adopted.

Add the states: pending, fulfilled, missing, unresolved. Add the ghost node on
the canvas for pending creates.

**What this alone gives:** waiting-on-code warnings, verification of finished
work, and the node-to-tasks lookup with modes. This is the phase where the
design stops being a task board.

### Phase 3 — the level board

Make the board show one level, with a breadcrumb, pinning, and the root level
that includes orphans. Add the work tree to the sidebar.

**What this alone gives:** the recursive model becomes usable at scale instead
of producing a crowded board.

### Phase 4 — readiness, conflicts, and suggestions

Add the dependency guards, computed readiness, rollup markers, contested
detection with the mode matrix, conflict decisions including resolution by
ordering, and the three suggestion helpers.

**What this alone gives:** the coordination features, which are the ones that
need the most data to be useful and therefore belong last.

```
   PHASE 1  ████░░░░░░░░  a planning tool
   PHASE 2  ████████░░░░  a planning tool that knows the code
   PHASE 3  ██████████░░  usable on a real project
   PHASE 4  ████████████  coordination and conflict
```

---

## 6. Places where the change is sharp

Three parts of the change are not purely additive, and each deserves a decision
in advance.

**Reads now go through the active version.** Anything that reads a task's
children today reads them from the task. After phase 1 it reads them from the
active version. This is a small change made in many places, and it is worth
routing every child read through one path early so the change happens once.

**Subtask order becomes meaningful.** Today a subtask set has no order, so
nothing depends on it. After phase 1 the order carries the author's advice about
sequence. People need to know that reordering is now a real edit rather than a
cosmetic one, which is a note in the interface rather than in the model.

**Dependency guards may reject edges that exist today.** The ancestor rule
forbids a task depending on its own parent, and it is possible that such an edge
already exists somewhere. The migration should look for them, list them, and let
somebody decide, rather than deleting them silently or leaving deadlocks in
place.

---

## 7. What to check before calling it done

Rather than a test plan, this is the set of statements that should be true
afterwards.

```
   every existing task has exactly one active version
   every existing subtask appears exactly once in its parent's child list
   opening a task that was never touched looks the same as it does today
   a task with anchors and no links still contributes to the hot count
   deleting a task still removes every reference to it, and never deletes
     its children
   a dependency that would deadlock is refused with a sentence naming the
     alternative
   a create link bound to a real node turns a finished task from
     "done" into "done, verified"
```

The last one is the interesting one to check first, because it is the smallest
end-to-end proof that the whole idea works: somebody plans a function, writes
it, the parser sees it, and the plan checks itself.

The final file, [16 — Open questions](16-open-questions.md), lists what this
design did not settle.
