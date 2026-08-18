# 01 — The Starting Graph

Before any work is planned, this is what the parser has produced. It is the
world that every task will point at.

```
   folder   app/
     │
     ├── file  app/models.py
     │     ├── class  User
     │     └── class  Post
     │
     ├── file  app/services.py
     │     ├── function  createPost()
     │     └── function  listPosts()
     │
     └── file  app/web.py
           └── function  renderPost()
```

Nine nodes. Three files, two classes, three functions, one folder.

## What is not in this picture

The `User` class has an id, a name, and a password field. The `Post` class has
an id, a title, and a body. **None of those appear anywhere in the graph**,
because a field is not a node.

```
   THE GRAPH KNOWS                    THE GRAPH DOES NOT KNOW
   ───────────────                    ───────────────────────
   class User exists                  User has a password field
   class Post exists                  Post has a title and a body
   createPost() exists                createPost() takes three arguments
   createPost() calls save()          the SQL it runs
```

This is a limit, and it shapes how work is written down. When a task is about a
field, the link points at the class that holds the field and the sentence
carries the detail.

```
   TASK  VN-16   "Add an author_id field to Post"

     link   modify   class  app.models.Post
     note   "adds author_id pointing at User, required, indexed"
```

The system knows the class is being changed, so it can warn anybody else who
plans to change the same class. What exactly changes inside it is written in
English, where it belongs.

## The nodes that do not exist yet

Every task in this example plans code that has not been written. Those planned
nodes are named before they exist, and the canvas draws them as ghosts next to
their intended parents.

```
   PLANNED, from the three tasks
   ─────────────────────────────
   file      app/auth.py                 from VN-1  Authentication
   function  app.auth.hash_password      from VN-4  Password hashing
   function  app.auth.current_user       from VN-5  Write current_user()
   function  app.web.renderLogin         from VN-6  Login page
   class     app.models.Comment          from VN-8  Comment model
   function  app.services.createComment  from VN-9  Comment write path
   function  app.services.listComments   from VN-10 Comment read path
   function  app.services.checkComment   from VN-22 Detect banned words
```

Eight planned nodes against nine real ones. Half of this project exists only as
intention, and the graph shows it:

```
   folder   app/
     ├── file  app/models.py
     │     ├── class  User
     │     ├── class  Post
     │     └── ◌ class  Comment              ← planned by VN-8
     │
     ├── file  app/services.py
     │     ├── function  createPost()
     │     ├── function  listPosts()
     │     ├── ◌ function  createComment()   ← planned by VN-9
     │     ├── ◌ function  listComments()    ← planned by VN-10
     │     └── ◌ function  checkComment()    ← planned by VN-22
     │
     ├── file  app/web.py
     │     ├── function  renderPost()
     │     └── ◌ function  renderLogin()     ← planned by VN-6
     │
     └── ◌ file  app/auth.py                 ← planned by VN-1
           ├── ◌ function  hash_password()   ← planned by VN-4
           └── ◌ function  current_user()    ← planned by VN-5
```

Two things follow from this picture, and both matter later.

**Readiness is visible without anybody coordinating.** Any task that needs a
ghost node is waiting, and the system knows it from the links alone.

**Duplicate work is visible before it happens.** If a second task planned to
create `app.models.Comment`, there would be two ghosts with the same name, and
that is a warning worth more than most code review.

Next: [02 — The three tasks](02-the-three-tasks.md).
