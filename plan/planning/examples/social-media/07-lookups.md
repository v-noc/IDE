# 07 — Every Lookup, Both Directions

This file collects every list the system can produce for this project. They all
come from the same stored data: child references, dependencies, and node links
with modes.

---

## Direction 1 — From work to code

### What does the whole comments tree touch?

```
   VN-3   Add comments                         effective links, rolled up
   ─────────────────────────────────────────────────────────────────────────
   CREATES    ◌ class     app.models.Comment            VN-3, VN-8
              ◌ function  app.services.createComment    VN-9
              ◌ function  app.services.listComments     VN-10
              ◌ function  app.services.checkComment     VN-22

   MODIFIES   ◌ class     app.models.Comment            VN-9
              ◌ function  app.services.createComment    VN-22, VN-30 ⚑
              ● function  app.web.renderPost            VN-12 ⚑, VN-23

   READS      ● class     app.models.Post               VN-3, VN-8, VN-9
              ● class     app.models.User               VN-3, VN-8
              ◌ function  app.auth.current_user         VN-9
              ◌ function  app.services.listComments     VN-12

   ANCHORED   ● folder    app/                          VN-3
```

Four new nodes, three existing nodes changed, four read. Nobody wrote this list
on VN-3; every row is traceable to the leaf that claimed it.

### What does one leaf touch?

```
   VN-9   Comment write path
   ─────────────────────────────────────────────────────────────────────────
   CREATES    ◌ function  app.services.createComment          pending
   MODIFIES   ◌ class     app.models.Comment                  pending
   READS      ● class     app.models.Post                     live
              ◌ function  app.auth.current_user               missing ⚠
```

Two of the four point at code that does not exist. That is what makes VN-9
show as waiting, and it is why the suggestion in
[05](05-dependencies-and-readiness.md) had something to offer.

---

## Direction 2 — From code to work

### Who is about to touch `class Post`?

```
   class  app.models.Post                                        ● live
   ─────────────────────────────────────────────────────────────────────────
   MODIFYING   VN-16  Add an author_id field    ● in progress  ▸ Posts
   READING     VN-3   Add comments              ○ to do        ▸ root
               VN-8   Comment model             ○ to do        ▸ Comments
               VN-9   Comment write path        ○ to do        ▸ Comments

   ◦ one task is rewriting this class while three others read it
```

This is the view that appears when somebody clicks the node on the canvas. It
crosses trees, because standing on a class you do not care which tree owns the
work.

### Who is about to touch `createComment()`?

```
   function  app.services.createComment                     ◌ planned
   ─────────────────────────────────────────────────────────────────────────
   CREATING    VN-9   Comment write path        ○ to do     ▸ Comments
   MODIFYING   VN-30  Rate limiting             ○ to do     ▸ root
               VN-22  Detect banned words       ○ to do     ▸ Comments ▸ Moderation

   ⏭ sequenced:  VN-9 → VN-30 → VN-22
```

Three tasks, one function that does not exist yet, and a settled order. Two of
those edges came from link analysis and one came from a human decision recorded
in [06](06-conflicts.md).

### Who is about to touch `renderPost()`?

```
   function  app.web.renderPost                                  ● live
   ─────────────────────────────────────────────────────────────────────────
   MODIFYING   VN-12  Show comments on the page   ○ to do   ▸ Comments
               VN-17  Show the author             ○ to do   ▸ Posts
               VN-23  Hide a comment              ○ to do   ▸ Comments ▸ Moderation

   ⚑ accepted on 14 Aug — "different parts of the same template"
```

Three tasks from three different places in the tree, all changing one function.
Without this list, the third one would be a surprise to the other two.

---

## Direction 3 — From code that does not exist yet

```
   PLANNED NODES, and who is planning them
   ─────────────────────────────────────────────────────────────────────────
   ◌ file      app/auth.py                    VN-1
   ◌ function  app.auth.hash_password         VN-4    ✓ now fulfilled
   ◌ function  app.auth.current_user          VN-5
   ◌ function  app.web.renderLogin            VN-6
   ◌ class     app.models.Comment             VN-8
   ◌ function  app.services.createComment     VN-9
   ◌ function  app.services.listComments      VN-10
   ◌ function  app.services.checkComment      VN-22
```

This list is what the canvas draws as ghosts, what produces duplicate warnings,
and what turns into verification when the code lands.

---

## Cross-tree lists

### Everything blocked, and by what

```
   VN-9    ⛔ VN-5   Write current_user()     ▸ Authentication
           ⛔ VN-8   Comment model            ▸ Add comments
   VN-10   ⛔ VN-8   Comment model            ▸ Add comments
   VN-12   ⛔ VN-10  Comment read path        ▸ Add comments
   VN-22   ⛔ VN-9   Comment write path       ▸ Add comments
           ⛔ VN-30  Rate limiting            ▸ root
   VN-30   ⛔ VN-9   Comment write path       ▸ Add comments
```

Every blocker carries a breadcrumb, because a key on its own does not tell you
where to go.

### Everything ready

```
   VN-5   Write current_user()      ▸ Authentication
   VN-6   Login page                ▸ Authentication
   VN-8   Comment model             ▸ Add comments
   VN-16  Add an author_id field    ▸ Posts belong to users
   VN-17  Show the author           ▸ Posts belong to users
   VN-11  Comment moderation        ▸ Add comments      (planning only)
```

### Everything a person could break by finishing it

```
   VN-9 is depended on by:   VN-22, VN-30
   VN-8 is depended on by:   VN-9, VN-10
   VN-5 is depended on by:   VN-9
   VN-10 is depended on by:  VN-12
   VN-30 is depended on by:  VN-22
```

The reverse view of the same six edges, computed rather than stored, which is
why it can never disagree with the forward view.

---

## The whole project on one screen

```
   TREE                                 STATE            TOUCHES
   ────                                 ─────            ───────
   VN-1  Authentication                 doing  1/3       app/auth.py ◌
     VN-4  Password hashing             done ✓ verified  hash_password ●
     VN-5  Write current_user()         ready            current_user ◌
     VN-6  Login page                   ready            renderLogin ◌

   VN-2  Posts belong to users          doing  0/2       class Post
     VN-16 Add an author_id field       doing            class Post ~
     VN-17 Show the author              ready            renderPost ~ ⚑

   VN-3  Add comments                   todo   0/5  🔴4
     VN-8  Comment model                ready            class Comment ◌
     VN-9  Comment write path           ⛔ 2              createComment ◌
     VN-10 Comment read path            ⛔ 1              listComments ◌
     VN-11 Comment moderation           ⑂2  ▸2
       VN-22 Detect banned words        ⛔ 2              checkComment ◌
       VN-23 Hide a comment             waiting          renderPost ~ ⚑
     VN-12 Show comments on the page    ⛔ 1              renderPost ~ ⚑

   VN-30 Rate limiting                  ⛔ 1              createComment ~ ⏭
```

Fifteen tasks, three levels, three trees, six dependencies, three collisions,
eight planned nodes. Everything in the state and touches columns is computed.
The stored data is only: the tasks, their versions, the ordered child lists,
six dependency edges, the links, and two conflict decisions.

Next: [08 — What each concept earned](08-what-each-concept-earned.md).
