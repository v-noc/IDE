# 02 — The Three Tasks

Three things need to happen. Each one is written as a root task, and each gets
children as somebody thinks it through.

```
   ROOT BOARD
   ┌────────────────────┬─────────────────┬──────────────────┐
   │ TO DO              │ IN PROGRESS     │ DONE             │
   ├────────────────────┼─────────────────┼──────────────────┤
   │ VN-3  Add comments │ VN-1  Auth      │                  │
   │ 0 of 5 · ▸ 5       │ 1 of 3 · ▸ 3    │                  │
   │                    │                 │                  │
   │ VN-30 Rate limiting│ VN-2  Posts     │                  │
   │                    │ belong to users │                  │
   │                    │ 0 of 2 · ▸ 2    │                  │
   └────────────────────┴─────────────────┴──────────────────┘
```

Four cards. That is the entire project at the top level, and it stays four
cards no matter how much detail is added underneath.

---

## VN-1 — Authentication

```
   TASK  VN-1   Authentication                              ● in progress
   ───────────────────────────────────────────────────────────────────────
   description   People can create an account, log in, and be recognised on
                 later requests.

   document      ## Approach
                 Passwords are hashed with a slow hash. Sessions are signed
                 cookies rather than tokens, because there is no second client
                 yet and cookies need no extra storage.
                 ## Rejected
                 JWT: nothing needs stateless verification, and revoking a
                 token would mean adding storage anyway.

   affects       + file  app/auth.py

   children      1  VN-4   Password hashing
                 2  VN-5   Write current_user()
                 3  VN-6   Login page

   location      app/          ← derived, not typed
```

VN-1 was created by right-clicking `app/` on the canvas and answering "will this
work read it, change it, or remove it?" with *change*, which wrote the one link
above. The location line is that link's container, worked out at read time
rather than typed by anybody.

The order says something real. Hashing comes first because the other two use
it. It does not block anything by itself, and the actual blocking comes from
the links, which is shown in [05](05-dependencies-and-readiness.md).

### Its children

```
   VN-4   Password hashing                                 ✓ done
     + function  app.auth.hash_password
     note on the link: "argon2, cost parameters in settings"

   VN-5   Write current_user()                             ○ to do
     + function  app.auth.current_user
     ◦ class     app.models.User
     note: "reads the signed cookie, returns the User or None"

   VN-6   Login page                                       ○ to do
     + function  app.web.renderLogin
     ~ file      app/web.py
     ◦ function  app.auth.hash_password
```

VN-4 is finished, and because it declared what it would create, the system
checked it: `app.auth.hash_password` now exists in the graph, so VN-4 reads
**done, verified**.

---

## VN-2 — Posts belong to users

```
   TASK  VN-2   Posts belong to users                       ● in progress
   ───────────────────────────────────────────────────────────────────────
   description   A post records who wrote it, and the post page shows the
                 author's name.

   document      ## Approach
                 Post gains an author_id pointing at User. Existing rows get
                 a placeholder account, since there is no way to recover who
                 wrote them.

   children      1  VN-16  Add an author_id field to Post
                 2  VN-17  Show the author on the post page

   location      app/models.py     ← derived from the children's links
```

### Its children

```
   VN-16  Add an author_id field to Post                   ● in progress
     ~ class     app.models.Post
     note: "author_id points at User, required, indexed. Existing rows get
            the placeholder account."
     ◦ class     app.models.User

   VN-17  Show the author on the post page                 ○ to do
     ~ function  app.web.renderPost
     ◦ class     app.models.User
```

This is the clearest example of the five-node-kinds rule doing its job. VN-16 is
entirely about a field, and it is recorded as an `affects` on the class with the
field described in a sentence. Nothing about that is lossy for a reader, and it
means the link can actually resolve.

It is also the case where `affects` on a container is genuinely correct. Adding
a field changes the class itself — its shape, its storage, its constructor — so
the claim is about `class Post`. Contrast that with adding a *method*, which is
a `create` link on the new function and leaves the class untouched.

It also creates the project's first quiet signal. VN-16 is rewriting `class
Post`, and two tasks in the comments tree plan to read it. That is a **watch**,
not a conflict, and it shows up as a small note rather than an alarm.

---

## VN-3 — Add comments

```
   TASK  VN-3   Add comments                                ○ to do
   ───────────────────────────────────────────────────────────────────────
   description   People can comment on a post, see other comments, and
                 comments can be moderated.

   location      —     nothing linked yet
```

At this moment VN-3 has no document, no links, and no children. It is a title
and a sentence, which is a perfectly legal state, and it is where most work
starts.

The empty location line is the point worth noticing. Nobody knows yet which code
this will touch, so nothing claims to. There is no way to write down a vague
gesture at `app/` that would *look* like the task is connected to the graph
while telling nobody anything — and an empty line is the truthful version of
"we have not worked this out yet".

VN-3 gets real links the moment somebody plans it, which is
[03 — Planning comments](03-planning-comments.md).

---

## VN-30 — Rate limiting

```
   TASK  VN-30  Rate limiting                               ○ to do
   ───────────────────────────────────────────────────────────────────────
   description   Stop one account from posting or commenting hundreds of
                 times a minute.

   affects       ~ function  app.services.createPost
                 ~ function  app.services.createComment      ← does not exist yet
```

VN-30 is a root task that belongs to none of the other three. It is here for
one reason: its second link points at a function that another tree is planning
to create, which sets up the collision in [06](06-conflicts.md).

Notice that VN-30 can record that link even though `createComment()` does not
exist. It is stored by name and kind, and it is already indexed, so the
collision will be found the moment the other side records the same name.

---

## What the board looks like at each level

```
   ▸ root                          4 cards
   ▸ root ▸ Authentication         3 cards   VN-4 · VN-5 · VN-6
   ▸ root ▸ Posts belong to users  2 cards   VN-16 · VN-17
   ▸ root ▸ Add comments           0 cards   nothing planned yet
```

Nine tasks exist. No screen ever shows more than four of them at once.

Next: [03 — Planning comments](03-planning-comments.md).
