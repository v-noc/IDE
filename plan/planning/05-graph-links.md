# 05 — Graph Links

This is the part of the design that the rest of the product cannot copy from
anywhere else. A task board that links work to code is not new. A task board
where the code graph can be asked *which work is about to touch this function,
and is anybody going to rewrite it* is new, and it only works if the links are
modelled carefully.

This file covers how work points at code, what happens when the code does not
exist yet, what happens when the parser deletes it, how links roll up a tree,
and how both lookup directions are answered.

---

## 1. The five node kinds, and why nothing else is allowed

The parser produces exactly five kinds of node.

```
   folder  ──contains──►  file  ──contains──►  class  ──contains──►  function
                                                                        │
                                                                   contains
                                                                        ▼
                                                                      call
```

That is the entire vocabulary. There is no node for a field, a column, a
parameter, an import, an endpoint, a route, a table, or a migration.

It is tempting to invent one, because plans talk about fields constantly. The
reason not to is simple and hard: **a link can only be checked if the thing it
points at is something the parser really produces.** A link to
`Comment.author_id` could never resolve, never turn green, never be verified,
and never take part in a collision check. It would look like data and behave
like a comment.

So the rule is:

> **The link says where. The task's own words say what.**

```
   TASK  VN-20   "Add author_id and post_id fields to Comment"

     link   mode: affects   kind: class   qname: app.models.Comment
     note   "adds author_id pointing at User and post_id pointing at Post,
             both required, both indexed"
```

Everything useful survives. The system knows the class is being affected, it
can warn if somebody else is also affecting that class, and a person reading
the card knows exactly which fields are involved because the sentence says so.

### Call nodes are a special case

Calls are produced by the parser, not written by people, and they appear and
disappear constantly as function bodies change. So calls may be used as
**context** — "read this call to understand how the current code flows" — but a
plan should not claim to create, affect, or delete a call directly. You affect
the function that contains the call, and the call follows.

The interface can allow an `affects` link on a call and quietly record it as an
`affects` on its parent function, which is what the person meant anyway.

---

## 2. The four modes

A task points at code in exactly one way: `node_links[]`. There are four modes,
and none of them is vague.

| Mode | Meaning | Where it appears | Is it a write? |
|---|---|---|---|
| `read` | Must be read to do the work, will not change | **Context** list | no |
| `create` | Does not exist yet, this work will create it | **Affects** list | yes |
| `affects` | This node's own body or signature changes | **Affects** list | yes |
| `delete` | Exists, this work will remove it | **Affects** list | yes |

```
   TASK VN-9  "Comment write path"

   CONTEXT                                  AFFECTS
   ───────                                  ───────
   read  ──► class    Post                  create  ──► function createComment()
   read  ──► class    User                  affects ──► class    Comment
   read  ──► function current_user()
```

The split into two lists is a display choice over one stored mechanism. That
matters because the most valuable question comes from the other direction, and
it needs one pass over one list rather than a merge of two.

### Every mode makes a checkable claim

There is no vague mode. A pointer that said only "this work is around here"
would never turn green, never conflict with anything, and never prove that
anything was done — it would look like data and behave like a comment.

Each of the four says something the graph can later confirm or contradict, which
is the whole point of planning on top of a graph rather than in a list of
sentences.

### A task may link to any number of nodes

There is no primary link and no limit.

```
   TASK VN-8  "Comment model"
     affects  class     Comment
     affects  class     Post
     create   function  Comment.validate
```

Which raises a question the modes do not answer on their own: *where does this
work live?*, for breadcrumbs and for placing a card on the canvas. That is
**derived** rather than recorded:

```
   take the nearest container holding every linked node
     │
     ├── specific  (a file, or a class)   ──►  show it as the location
     └── too broad (a top folder, the repo) ──►  show the linked nodes instead
```

Display rule only. Nothing is stored for it, nothing has to be maintained by
hand, and the location can never drift out of step with the code the task
actually touches.

---

## 3. `affects` means the node itself, never its contents

> Changes to a node's **contents** are derived from the links on those contents.
> They are never typed on the container.

Adding a method to a class is **one** link:

```
   TYPED
     create   function  Comment.validate     container: class Comment

   DERIVED
     touches  class Comment      it contains the new function
     touches  file  models.py    it contains Comment
```

Write `affects class Comment` only if the class itself also changes — a new
field, a changed base class, a decorator.

### Why this rule is required

Without it, two tasks each adding a *different* method to `Comment` would both
write "affects class Comment", and the system would report them as colliding.

```
   WITHOUT THE RULE                      WITH THE RULE
   ────────────────                      ─────────────
   VN-8   affects class Comment          VN-8   create function Comment.validate
   VN-44  affects class Comment          VN-44  create function Comment.render

   ⚑ conflict — but there is none        no conflict. Two different functions.
                                         Both still show up when you ask what
                                         touches class Comment, as derived
                                         containment.
```

They do not collide. Every class in the codebase would become a false alarm, and
a warning that is usually wrong is a warning people learn to click past.

### The limit, stated plainly

**Derived containment never verifies anything.** Only explicit links have states.

A class is not verified because a function inside it appeared. If a task wants
its claim about `class Comment` checked, it has to make that claim directly with
an `affects` link — which is exactly the right thing to require, because "the
class changed" and "something inside the class changed" are different statements.

### Getting the mode wrong is recoverable

People will mark something `read` and then change it anyway. This does not
corrupt anything, because after the work lands the commits say which nodes
actually changed. Comparing the two produces a useful, gentle observation:

```
   VN-9 marked class Post as read, but the commits for this task changed it.
   Update the link to affects?     [ yes ]  [ it was a one-off, ignore ]
```

A mistake that can be noticed and corrected is a much better position than a
model that never asked for the distinction at all.

---

## 4. Links can point at code that does not exist yet

This is the core of planning. When you plan, most of the interesting code has
not been written.

A `create` link names the node it intends to bring into existence, using the
name and kind it will have.

```
   create   kind: class      qname: app.models.Comment            node_id: —
   create   kind: function   qname: app.services.createComment    node_id: —
```

The `node_id` is empty because there is no node. The `qname` and `kind` are
enough to display the link, to compare it against other tasks, and later to
recognise the node when it appears.

### The life of a create link

```
   ┌──────────┐   the work is done, the parser   ┌────────────┐
   │ pending  │─────── sees a new node ─────────►│ fulfilled  │
   └──────────┘        with that name            └────────────┘
        │
        │ nobody ever writes it, and the task is closed
        ▼
   ┌────────────────────────────┐
   │ done, unverified           │  ← the honest state, never hidden
   └────────────────────────────┘
```

Binding happens by matching the name and the kind. When a class named
`app.models.Comment` appears in the graph and a pending create link is waiting
for exactly that name and kind, the link picks up the real node id and turns
green.

**Tradeoff, stated honestly.** Matching by name is a guess. If somebody plans
`app.models.Comment` and writes `app.models.PostComment`, the link stays pending
even though the work is finished. The system handles this by offering the
closest new nodes created around the same time as candidates, reusing the
matcher that already suggests replacements for a link whose node disappeared.
Automatic binding is only applied for an exact match on name and kind, and
everything else is a suggestion a person confirms. Silently binding a plan to
the wrong node would be far worse than leaving a link pending.

### Create link identity: (qname, kind)

A create link's identity is its **intended name and kind**, not a node id
(which does not exist yet). This means create links are indexed two ways:

**By node_id** — for fulfilled links that point at a real node.
**By (qname, kind)** — for pending links waiting for a node to appear.

When looking up tasks that touch a particular node, the system checks both
indexes. This is what surfaces "someone plans to create something here" before
it exists.

```
   unfulfilled link index              fulfilled link index
   ─────────────────────              ────────────────────
   (app.models.Comment, class) → VN-8  node_abc123 → VN-16 (create)
                              → VN-44  node_def456 → VN-9  (affects)
```

### Binding a create link to the real node

When the parser produces a node matching both the qname and kind, the link
binds automatically. **The first binding writes an event** carrying the node id,
kind, and graph revision:

```
{ type: "verified",
  payload: {
    link_qnames: ["app.models.Comment"],
    node_ids: ["node_abc123"],
    graph_revision: "xyz789"
  },
  at: ..., author: ... }
```

Recording the graph revision means a task verified at one moment in time stays
marked verified even if the node is later deleted and recreated. The task shows
"verified at revision xyz789, node since removed" rather than silently
un-verifying.

### Four edge cases handled explicitly

**Node already exists when the create link is written.** Warn: "app.models.Comment already exists — did you mean affects?" Do not create a link that fulfils instantly. The distinction between create and affects matters.

**Two open tasks plan to create the same qname and kind.** Duplicate warning, not a dependency. This fires at planning time, before merge conflicts. One task is probably unnecessary, but the system shows both and lets a human decide.

**Container doesn't exist either** (new class in a new file). Fine. Two pending creates, no ordering needed, both fulfil together when the file appears in the graph.

**A node appears at the qname but with wrong kind.** Do not fulfil. Show as a mismatch — the plan or the implementation drifted. Offer a rebind.

### Rebind suggestions for broken links

A link breaks when its node is deleted or renamed. The system offers a one-click
rebind when a new node appears with:
- Similar leaf name (edit distance)
- Same kind
- Same container (same file/class)
- Nothing else linking to it yet

Example:

```
   Link broke:     affects function app.services.createComment
   Suggestion:     affects function app.services.create_comment  (snake_case typo)
   [ rebind to suggestion ]  [ manually choose another ]  [ remove link ]
```

Suggest, never bind silently. A wrong rebind silently changes what the task means.

### Restrict which kinds are linkable

`call` nodes churn constantly as function bodies change. Linking to calls is
rarely meaningful. Restrict `create`, `affects`, and `delete` to:

```
   create / affects / delete:   folder, file, class, function
   read:                        all five kinds, including call
```

This prevents the long tail of broken links to deleted calls from cluttering
the interface.

### Ghost nodes on the canvas

Render a pending create as a dashed node in its container's position on the
canvas. It is the cheapest visual proof that the plan and the graph are the
same object — you watch it turn solid when the code lands.

```
   file  app/models.py
     ├── class  Post           ▮ solid
     ├── class  User           ▮ solid
     └── class  Comment        ▯ dashed (pending, VN-8 plans to create)
```

### Two tasks that both plan to create the same node

If two pending create links name the same thing, that is one of the strongest
signals the system can produce, because it usually means two people are about
to write the same class without knowing about each other.

```
   pending create  ──► class app.models.Comment  ── VN-8   Comment model
   pending create  ──► class app.models.Comment  ── VN-44  Comment storage

   ⇒ duplicate work warning, before either of them has written a line
```

This is worth more than most conflict detection, because it fires at planning
time rather than at merge time.

---

## 5. When the graph changes underneath a link

The parser rewrites the graph whenever a file changes. Nodes are deleted and
recreated all the time. Every pointer from work into the graph is therefore
stored as a **soft id plus a snapshot of the name and kind**.

```
   STORED           node_id: FunctionSchema/abc123
                    qname:   app.services.createPost
                    kind:    function
```

When the node id no longer names anything, the link does not break. It becomes
**unresolved**, and it still reads sensibly because the snapshot is right there.

```
   ┌────────────────────────────────────────────────────┐
   │ ⚠ affects   function app.services.createPost         │
   │   this node no longer exists in the graph           │
   │   [ point at another node ]   [ remove the link ]   │
   └────────────────────────────────────────────────────┘
```

The three ordinary reasons a node disappears each have a sensible answer.

| What happened | What the system does |
|---|---|
| Renamed | Suggests nodes with a similar name and the same kind, ranked by closeness |
| Moved to another file | Suggests nodes with the same short name anywhere in the graph |
| Genuinely deleted | Offers to remove the link, or to change it into a `delete` link, which may be exactly what the work was |

No automatic re-pointing happens. Quietly moving a plan from one function to
another changes what the plan means, and a visible warning is much better than
a confident lie.

---

## 6. Verification, and its second source

A `create` link that binds to a real node is the system checking a claim rather
than believing it. That check is worth being careful about in two ways.

### Verification is stamped, not recomputed forever

If `verified` were recomputed on every read, a rename six months later would
silently un-verify finished work. Verification is a **decision at a point in
time** — somebody finished this, and the graph agreed — so it is recorded as an
event:

```
   { type: "verified",
     payload: { link_qnames: [...], node_ids: [...], graph_revision: "xyz789" },
     at, origin, author }
```

A task shows "done, verified" if that event exists. If a verified link later
goes unresolved, the panel says:

```
   ✓ done · verified at revision xyz789
   ⚠ function app.services.createComment has since been removed
```

That is a note, not a reversal. The work was done; the codebase moved on. Those
are two different facts and the interface shows both.

### Tests are the second source

The design's honest weakness, named in [14](14-edge-cases.md) §12, is that it
tracks **identity, not meaning**. A function rewritten in place still satisfies
every link pointing at it, so structural verification cannot tell the difference
between "this was built" and "this still does what it said".

The repo already tracks tests. So a task may optionally name the test nodes that
must pass:

```
   TASK VN-9  "Comment write path"
     verified_by_tests
       function tests.services.test_create_comment_attaches_author
       function tests.services.test_create_comment_rejects_missing_post
```

This does two things that link verification cannot.

**It closes the rewritten-in-place hole.** A rewrite that changes behaviour
breaks the tests, and the task stops being verified for a reason that is about
meaning rather than structure.

**It gives verification to work with no graph trace at all.** Documentation,
configuration, and conversations create no nodes, so they have nothing to check.
Today those tasks are simply done with nothing to verify, and the interface must
never treat that as a warning. A task that names a test has something real to
check even when it creates no code.

Both sources are optional and neither is a gate. A task with no links and no
tests is finished when a person says it is finished.

---

## 7. Links roll up the tree

Nobody wants to write links twice. A parent's **effective links** are its own
links combined with every descendant's links.

```
   VN-3  Add comments                    own links: none
     ├── VN-8   Comment model            create class Comment
     ├── VN-9   Comment write path       create function createComment()
     │                                    affects class Comment
     └── VN-12  Show comments on page    affects function renderPost()

   EFFECTIVE LINKS OF VN-3, computed:
     create  class    Comment              from VN-8
     create  function createComment()      from VN-9
     affects  class    Comment              from VN-9
     affects  function renderPost()         from VN-12
```

This is why nobody has to maintain links on high level tasks. A card near the
root can honestly say what its whole subtree touches, and every entry can be
traced back to the leaf that claimed it.

When the same node appears more than once, the strongest mode wins for display
purposes, in the order `delete` beats `affects`, which beats `create`, which
beats `read`. The individual entries are all kept underneath, because knowing
*which* leaf reads a node and which one rewrites it is the whole point.

---

## 8. The two lookups

Everything above exists to make these two questions cheap.

### Task to nodes: what does this work touch?

```
   VN-3  Add comments
   ─────────────────────────────────────────────────────────────
   CREATES      class    app.models.Comment           pending
                function app.services.createComment   pending
   AFFECTS      class    app.models.Comment           live
                function app.web.renderPost           live
   READS        class    app.models.Post              live
                class    app.models.User              live
                function app.auth.current_user        pending  ← from another task

   LOCATION     folder   app/comments        ← derived, nearest common container
```

That list is assembled from VN-3's own links and those of everything underneath
it. A person can look at one card and know the blast radius of the work before
starting it.

The last row is not stored. `app/comments` is simply the nearest container that
holds every node above it, worked out at read time.

### Node to tasks: who is about to touch this?

```
   class  app.models.Post
   ─────────────────────────────────────────────────────────────
   AFFECTING    VN-16  Add author to posts        ● in progress
   READING      VN-9   Comment write path         ○ to do
                VN-10  Comment read path          ○ to do
   ABOUT        VN-2   Posts belong to users      ● in progress

   ⚑ one task is rewriting this class while two others are reading it
```

This is the view that appears on the canvas when somebody clicks a node badge,
in the sidebar tree, and in the task detail panel. It is one index lookup, and
[09 — Architecture](09-architecture.md) describes how it is kept fast.

Notice that the second list includes tasks from anywhere in the tree. That is
deliberate. When you are standing on a class, you do not care which epic owns
the work; you care that somebody is about to rewrite the class you are reading.

---

## 9. What the modes make possible

Putting the mode on the link is what turns a list of connections into something
that can answer questions. Three examples, each of which is impossible without
modes:

```
   TWO WRITERS               VN-11 affects createComment()
                             VN-30 affects createComment()
                             ⇒ collision. See 08.

   READER UNDER A WRITER     VN-16 affects   class Post
                             VN-9  read     class Post
                             ⇒ VN-9's assumptions may expire. Worth a note,
                               not a block.

   NEED BEFORE EXISTENCE     VN-9  read     function current_user()  pending
                             VN-5  create   function current_user()  pending
                             ⇒ VN-9 needs what VN-5 will make.
                               Suggest a dependency. See 06.
```

The third one is the most valuable, because it turns dependency management from
something people have to remember into something the system notices.

---

## 10. Costs of this approach

**People have to write links.** This is real work, and if it is tedious it will
not happen. Three things reduce it: creating a task from a node on the canvas
fills in the first link automatically, the graph can suggest links from the
callers and callees of nodes already linked, and links roll up so only leaves
need them.

**Names are not stable.** Binding a pending create by name is a guess, and
renames break links. The design accepts visible warnings rather than clever
automatic repair, because a wrong automatic repair is undetectable while a
warning is merely annoying.

**Rollup costs reads.** Computing a parent's effective links means walking its
subtree. This is handled by computing one summary per board level in a single
pass, described in [09](09-architecture.md).

**Not all work has a graph trace.** Documentation, configuration, and
discussions have no nodes. Those tasks simply have no links, and the interface
must never treat an empty Affects list as a problem. `verified_by_tests` is the
optional escape hatch for the ones that do have something checkable.

The next file, [06 — Dependencies and readiness](06-dependencies-and-readiness.md),
uses the link states defined here to work out what somebody can actually start
right now.
