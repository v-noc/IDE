# 03 — Planning the Comments Task

VN-3 was a title and one sentence. Somebody now sits down and plans it. This
file shows what gets written, what the system does with it, and how the tree
reaches three levels without the board getting crowded.

---

## What gets written

```
   TASK  VN-3   Add comments
   ACTIVE VERSION  v1  "Separate Comment class"
   ────────────────────────────────────────────────────────────────────────
   summary     Comments are their own class, linked to a post and an author,
               stored in their own table.

   document    ## Approach
               A Comment class holds the post it belongs to, the account that
               wrote it, the body text, and when it was written. The service
               layer owns validation and the repository owns storage, matching
               how posts already work.

               ## Why not store them inside Post
               Posts would grow without limit, moderation would have to rewrite
               the whole post row, and listing recent comments across posts
               would become a scan. That approach is written down as v2 so the
               reasoning is not lost.

               ## Moderation
               Deliberately left as its own task. There is a real choice there
               and it should not be buried inside this document.

   context     ◦ class  app.models.Post
               ◦ class  app.models.User

   affects     + class  app.models.Comment
               note: "post_id, author_id, body, created_at"

   children    1  VN-8   Comment model
               2  VN-9   Comment write path
               3  VN-10  Comment read path
               4  VN-11  Comment moderation
               5  VN-12  Show comments on the post page
```

Two things about that document are worth pointing out, because they are the
habits the whole design is trying to encourage.

**The rejected approach is written down, not deleted.** It also exists as a
real second version, which is [04](04-alternative-versions.md).

**The moderation decision is pushed down, not buried.** The document says a
choice exists and names where it lives, and the choice itself becomes two
versions on VN-11.

---

## The children

```
   VN-8    Comment model                                   ○ to do
     + class     app.models.Comment
       note: "post_id required, author_id required, body text, created_at"
     ◦ class     app.models.Post
     ◦ class     app.models.User

   VN-9    Comment write path                              ○ to do
     + function  app.services.createComment
     ~ class     app.models.Comment
     ◦ class     app.models.Post
     ◦ function  app.auth.current_user
       note: "the comment's author is whoever is logged in"

   VN-10   Comment read path                               ○ to do
     + function  app.services.listComments
     ◦ class     app.models.Comment

   VN-11   Comment moderation                              ○ to do
     (two versions, see below)

   VN-12   Show comments on the post page                  ○ to do
     ~ function  app.web.renderPost
     ◦ function  app.services.listComments
```

Every one of those is a leaf except VN-11. Each describes one coherent change
that fits in a sentence, which is the stopping rule from the mental model.

Notice what is **not** a task. Nobody created "add the post_id field", "add the
author_id field", "add the body field", and "add the created_at field". Those
are four sentences in one note on one link, and splitting them into four cards
would produce four statuses, four positions, and no extra information.

---

## VN-11 grows a real decision inside it

```
   TASK  VN-11   Comment moderation                        ○ to do
   ▸ root ▸ Add comments ▸ VN-11
   ────────────────────────────────────────────────────────────────────────
   ⑂ v1  Keyword filter  ★active   |   v2  Manual review queue

   v1  Keyword filter
       summary   A comment is checked against a word list when it is saved.
                 Failing comments are hidden immediately.
       document  Ships this week. No new screens. It will produce false
                 positives, which is acceptable while volume is low.
       affects   + function  app.services.checkComment
                 ~ function  app.services.createComment
       children  1  VN-22  Detect banned words
                 2  VN-23  Hide a comment from the post page

   v2  Manual review queue
       summary   Reported comments go into a queue that a moderator works
                 through.
       document  Better outcomes, needs an admin screen and a permissions
                 idea that does not exist yet. Written down so the choice is
                 recorded rather than argued about again in a month.
       affects   + class     app.models.Report
                 + function  app.web.renderModerationQueue
       children  1  VN-24  Report a comment
                 2  VN-25  Moderation queue page
```

This is the recursion doing its job. VN-11 was one line in somebody's plan.
When it turned out to contain a genuine decision, it got versions and children,
using the same operations as any other task. Nothing was converted, and nothing
had to be promoted from one type to another.

The decision lives at the level where the choice actually is, which is three
levels down. The parent did not need alternatives just because a child has
them.

---

## The tree now

```
   VN-1   Authentication                    ● in progress   1 of 3
     ├── VN-4   Password hashing            ✓ done · verified
     ├── VN-5   Write current_user()        ○ to do
     └── VN-6   Login page                  ○ to do

   VN-2   Posts belong to users             ● in progress   0 of 2
     ├── VN-16  Add an author_id field      ● in progress
     └── VN-17  Show the author             ○ to do

   VN-3   Add comments                      ○ to do         0 of 5
     ├── VN-8   Comment model               ○ to do
     ├── VN-9   Comment write path          ○ to do
     ├── VN-10  Comment read path           ○ to do
     ├── VN-11  Comment moderation          ○ to do    ⑂ 2 versions
     │     ├── VN-22  Detect banned words   ○ to do
     │     └── VN-23  Hide a comment        ○ to do
     └── VN-12  Show comments on the page   ○ to do

   VN-30  Rate limiting                     ○ to do
```

Fifteen tasks, three levels deep. The root board still shows four cards.

```
   ▸ root                                   4 cards
   ▸ root ▸ Add comments                    5 cards
   ▸ root ▸ Add comments ▸ Moderation       2 cards
```

---

## What VN-3 touches, without anybody writing it there

VN-3's own version declares one create link. Everything else is rolled up from
its descendants.

```
   EFFECTIVE LINKS OF VN-3

   creates    class     app.models.Comment            VN-3 itself, VN-8
              function  app.services.createComment    VN-9
              function  app.services.listComments     VN-10
              function  app.services.checkComment     VN-22

   modifies   class     app.models.Comment            VN-9
              function  app.services.createComment    VN-22
              function  app.web.renderPost            VN-12, VN-23

   reads      class     app.models.Post               VN-3, VN-8, VN-9
              class     app.models.User               VN-3, VN-8
              function  app.auth.current_user         VN-9
              function  app.services.listComments     VN-12
```

Somebody standing on the root board can select VN-3 and see the full blast
radius of the comments work before any of it is written: four new nodes, three
existing nodes changed, four read. Nobody maintained that list. Every row can be
traced to the leaf that claimed it.

One row in it is doing quiet work already. `app.auth.current_user` is read by
VN-9 and does not exist, and something in another tree is planning to create
it. That is where [05](05-dependencies-and-readiness.md) starts.

Next: [04 — Alternative versions](04-alternative-versions.md).
