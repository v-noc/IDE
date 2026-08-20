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

     link   mode: modify   kind: class   qname: app.models.Comment
     note   "adds author_id pointing at User and post_id pointing at Post,
             both required, both indexed"
```

Everything useful survives. The system knows the class is being modified, it
can warn if somebody else is also modifying that class, and a person reading
the card knows exactly which fields are involved because the sentence says so.

### Call nodes are a special case

Calls are produced by the parser, not written by people, and they appear and
disappear constantly as function bodies change. So calls may be used as
**context** — "read this call to understand how the current code flows" — but a
plan should not claim to create, modify, or delete a call directly. You modify
the function that contains the call, and the call follows.

The interface can allow a `modify` link on a call and quietly record it as a
`modify` on its parent function, which is what the person meant anyway.

---

## 2. The modes

| Mode | Meaning | Where it appears | Is it a write? |
|---|---|---|---|
| `about` | This work is around here somewhere | anchor chip on the task | no |
| `read` | Must be read to do the work, will not change | **Context** list | no |
| `create` | Does not exist yet, this work will create it | **Affects** list | yes |
| `modify` | Exists, this work will change it | **Affects** list | yes |
| `delete` | Exists, this work will remove it | **Affects** list | yes |

```
   VERSION 1 of VN-9  "Comment write path"

   CONTEXT                                  AFFECTS
   ───────                                  ───────
   read  ──► class    Post                  create ──► function createComment()
   read  ──► class    User                  modify ──► class    Comment
   read  ──► function current_user()
```

The split into two lists is a display choice over one stored mechanism. That
matters because the most valuable question comes from the other direction, and
it needs one pass over one list rather than a merge of two.

### Getting the mode wrong is recoverable

People will mark something `read` and then change it anyway. This does not
corrupt anything, because after the work lands the commits say which nodes
actually changed. Comparing the two produces a useful, gentle observation:

```
   VN-9 marked class Post as read, but the commits for this task changed it.
   Update the link to modify?     [ yes ]  [ it was a one-off, ignore ]
```

A mistake that can be noticed and corrected is a much better position than a
model that never asked for the distinction at all.

---

## 3. Links can point at code that does not exist yet

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
closest new nodes created around the same time as candidates, in exactly the
same way the existing re-anchor flow suggests replacements for a lost anchor.
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
                              → VN-44  node_def456 → VN-9  (modify)
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

**Node already exists when the create link is written.** Warn: "app.models.Comment already exists — did you mean modify?" Do not create a link that fulfils instantly. The distinction between create and modify matters.

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
   Link broke:     modify function app.services.createComment
   Suggestion:     modify function app.services.create_comment  (snake_case typo)
   [ rebind to suggestion ]  [ manually choose another ]  [ remove link ]
```

Suggest, never bind silently. A wrong rebind silently changes what the task means.

### Restrict which kinds are linkable

`call` nodes churn constantly as function bodies change. Linking to calls is
rarely meaningful. Restrict `create`, `modify`, and `delete` to:

```
   linkable:     folder, file, class, function
   read only:    call
   anchors:      all kinds via mode "about"
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

## 4. When the graph changes underneath a link

The parser rewrites the graph whenever a file changes. Nodes are deleted and
recreated all the time. Every pointer from work into the graph is therefore
stored as a **soft id plus a snapshot of the name and kind**, exactly as anchors
already are today.

```
   STORED           node_id: FunctionSchema/abc123
                    qname:   app.services.createPost
                    kind:    function
```

When the node id no longer names anything, the link does not break. It becomes
**unresolved**, and it still reads sensibly because the snapshot is right there.

```
   ┌────────────────────────────────────────────────────┐
   │ ⚠ modify   function app.services.createPost         │
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

## 5. Links roll up the tree

Nobody wants to write links twice. A parent's **effective links** are its own
links combined with every descendant's links.

```
   VN-3  Add comments                    own links: none
     ├── VN-8   Comment model            create class Comment
     ├── VN-9   Comment write path       create function createComment()
     │                                    modify class Comment
     └── VN-12  Show comments on page    modify function renderPost()

   EFFECTIVE LINKS OF VN-3, computed:
     create  class    Comment              from VN-8
     create  function createComment()      from VN-9
     modify  class    Comment              from VN-9
     modify  function renderPost()         from VN-12
```

This is why nobody has to maintain links on high level tasks. A card near the
root can honestly say what its whole subtree touches, and every entry can be
traced back to the leaf that claimed it.

When the same node appears more than once, the strongest mode wins for display
purposes, in the order `delete` beats `modify`, which beats `create`, which
beats `read`, which beats `about`. The individual entries are all kept
underneath, because knowing *which* leaf reads a node and which one rewrites it
is the whole point.

---

## 6. The two lookups

Everything above exists to make these two questions cheap.

### Task to nodes: what does this work touch?

```
   VN-3  Add comments
   ─────────────────────────────────────────────────────────────
   CREATES      class    app.models.Comment           pending
                function app.services.createComment   pending
   MODIFIES     class    app.models.Comment           live
                function app.web.renderPost           live
   READS        class    app.models.Post              live
                class    app.models.User              live
                function app.auth.current_user        pending  ← from another task
   ANCHORED     folder   app/comments
```

That list is assembled from the active version of VN-3 and of everything
underneath it. A person can look at one card and know the blast radius of the
work before starting it.

### Node to tasks: who is about to touch this?

```
   class  app.models.Post
   ─────────────────────────────────────────────────────────────
   MODIFYING    VN-16  Add author to posts        ● in progress
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

## 7. What the modes make possible

Putting the mode on the link is what turns a list of connections into something
that can answer questions. Three examples, each of which is impossible without
modes:

```
   TWO WRITERS               VN-11 modify createComment()
                             VN-30 modify createComment()
                             ⇒ collision. See 08.

   READER UNDER A WRITER     VN-16 modify   class Post
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

## 8. Costs of this approach

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
must never treat an empty Affects list as a problem.

The next file, [06 — Dependencies and readiness](06-dependencies-and-readiness.md),
uses the link states defined here to work out what somebody can actually start
right now.
