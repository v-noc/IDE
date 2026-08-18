# Worked Example — A Small Social Media Application

This folder runs the whole design over one small project. Every concept from
the design files appears here doing real work, with concrete names, concrete
nodes, and concrete lists.

The application starts with users and posts. Three pieces of work are added:
people should be able to log in, posts should know who wrote them, and posts
should have comments.

That is enough to exercise everything: a tree several levels deep, two
competing approaches, code that does not exist yet, dependencies discovered
from the graph, two collisions resolved in two different ways, and both lookup
directions.

## Read in this order

```
examples/social-media/
│
├── 01-starting-graph.md
│      The code that already exists, as graph nodes. Five node kinds only.
│
├── 02-the-three-tasks.md
│      The three root tasks, and how they were written down.
│
├── 03-planning-comments.md
│      The comments task planned properly: document, context, affects, and
│      an ordered list of children. The tree grows to three levels.
│
├── 04-alternative-versions.md
│      A second approach to comments, compared side by side, and what happens
│      when it is activated and then reverted.
│
├── 05-dependencies-and-readiness.md
│      Every dependency in the project, where each came from, and exactly
│      what can be started on day one.
│
├── 06-conflicts.md
│      Two collisions. One resolved by deciding the order, one accepted.
│
├── 07-lookups.md
│      Every list the system can produce, in both directions.
│
└── 08-what-each-concept-earned.md
       A concept-by-concept account of what would have been lost without it.
```

## The cast

```
   TASKS                                NODES THAT EXIST AT THE START
   ─────                                ─────────────────────────────
   VN-1   Authentication                folder    app/
   VN-2   Posts belong to users           file    app/models.py
   VN-3   Add comments                      class   User
   VN-30  Rate limiting                     class   Post
                                          file    app/services.py
                                            function createPost()
                                            function listPosts()
                                          file    app/web.py
                                            function renderPost()
```

Everything else in this example is planned before it exists, which is the
point.
