# 12 — Agent Seams

The agent is not designed here. What is designed here is the set of openings the
model has to leave so that an agent can be added later without reshaping
anything.

The test used throughout is simple: **an agent should be able to do exactly what
a person does, through exactly the same records, and its work should be
reviewable by a person who was not watching.**

---

## 1. What a coding agent actually needs

Strip away the differences between Claude Code, Cursor, and the rest, and every
one of them needs four things while working.

```
   A WORK LIST     what to do, in an order, small enough to finish one at a time
   SCOPE           which code this piece of work is allowed to touch
   CONTEXT         which code must be read first to do it correctly
   A WAY TO SAY    what it did, so a human can check
```

Today those tools hold all four in a todo list of sentences that lives for one
session and then disappears. It works, and it is also the weakest part of the
loop, because a sentence cannot be checked, cannot be scoped, and cannot be
picked up by somebody else tomorrow.

Every one of the four already exists in this model, and each is more than a
sentence.

| The agent needs | This model already has |
|---|---|
| a work list | the task's children, ordered by `position` |
| scope | the affects list, with modes |
| context | the context list, plus the task's document |
| a way to say what it did | link states, and the graph itself as the check |

That is the whole argument for building the planning layer before the coding
agent. The agent does not need a todo feature; it needs this.

---

## 2. The three things an agent can be

### A reader

The simplest and least risky role. The agent is asked a question and reads the
work tree to answer it: what is ready to start, what is blocked and why, what
touches this class, what did we decide about the moderation approach.

The seam needed: **every derived value must be available as data, not only as a
screen.** The three summaries in [09](09-architecture.md) are what a reading
agent consumes, and they are the same ones the interface uses, so the agent and
the person are never looking at different answers.

### A planner

The agent is given a task and proposes how to do it: a document, context links,
affects links, and an ordered set of children.

There are no draft versions to hide the proposal in, so the review gate is built
out of the model's own parts.

**An agent proposes into a separate task, not into the real one.** The agent
creates a *proposal task* whose children are the steps it suggests. A proposal
task is an ordinary task in every respect, which means it can be read, edited,
commented on, and deleted with one cascade if it is rejected.

```
   agent writes ──► TASK "Proposal: comment write path"   created_by: run 4f2a
                    ├── child  Write createComment()
                    ├── child  Validate the post exists
                    └── document explaining the approach
                    │
                    │  a person reads it and edits it
                    ▼
   ACCEPT   reparent its children under the real task, copy the document across,
            delete the proposal
   REJECT   delete the proposal — one cascade, soft, undoable
```

This is the same review gate the grouper tool already uses — propose, show, wait
for approval — built without a draft state that the rest of the model would have
to know about.

**`created_by` names the run.** Every task, link, and event records who made it,
and an agent run is a valid author. So a person can see which parts of a plan
were proposed rather than written, and a plan can be filtered by author when
reviewing.

### An executor

The agent is given one task and does the work. This is the role that needs the
most care, and the model gives it three things a sentence list cannot.

**A bounded work item.** One leaf task, with a document explaining it and a
position in an order. Not "implement comments", but "write createComment() in
the service layer, validating that the post exists".

**A declared scope.** The affects list says which nodes this task may create,
change, or delete. Whether that becomes an enforced boundary or a reported one
is a decision for whoever builds the agent, and the model supports either: it
records intent, and afterwards the commits say what actually happened.

```
   DECLARED            create   function app.services.createComment
                       affects   class    app.models.Comment

   WHAT THE RUN DID    created  function app.services.createComment   ✓
                       affected class    app.models.Comment           ✓
                       affected class    app.models.Post              ← not declared
```

That last line is the useful one. It is not necessarily wrong; it is
necessarily worth a look.

**A verification signal.** When the run finishes, every `create` link either
points at a real node or does not. The agent does not get to grade its own work
by ticking a box, because the graph is the grader.

---

## 3. Where the agent puts what it learns

An agent that plans well often discovers things while working: this function is
messier than expected, this class is used in three places nobody mentioned, this
step turned out to need two steps.

Every one of those has an existing place to go, and none of them needs a new
concept.

| Discovery | Where it goes |
|---|---|
| this step needs sub-steps | children on the task, in order |
| I had to read this class too | a `read` link |
| I ended up changing something extra | a `affects` link, with a note |
| this approach will not work | a comment event, and a proposal task if it has a better idea |
| this cannot start until that lands | a suggested dependency, offered to a person |
| I am not sure about this decision | a comment event on the task, naming what it is unsure about |

The fact that all six land somewhere without inventing anything is the sign the
model is agent-ready. If an agent's normal discoveries had nowhere to go, they
would end up in chat transcripts, which nobody reads afterwards.

---

## 4. Undo, and why runs matter

Because work lives in the same database as the code graph, a run's writes are
commits. That means an agent run can be undone as a range, which is
the same mechanism the existing write tools use.

The seam this requires: **every write an agent makes carries its run id**, so
"undo everything run 4f2a did to the plan" is answerable. Without it, an agent's
edits and a person's edits mix into one history that cannot be separated.

---

## 5. Two agents at once

Nothing in the model assumes one agent. Two agents planning or executing at the
same time produce exactly the situation [08](08-conflicts-and-concurrency.md)
already describes, and the same four resolutions apply.

```
   agent A executing VN-30, declared:  affects createComment()
   agent B executing VN-11, declared:  affects createComment()

   ⚑ contested, visible to both, and to any person watching

   resolutions available:
     order them        → a real dependency, B waits
     accept            → a person says it is fine, with a reason
```

The valuable property is that this is visible **before either run starts
writing**, because both declared their intentions during planning. Agents that
keep their plans in session memory can only discover this by colliding.

---

## 6. What the model deliberately does not decide

These are real questions, and every one of them belongs to the agent design
rather than to the planning model.

**Whether scope is enforced or only reported.** The model records declared
scope and observed scope. Whether an agent is prevented from touching an
undeclared node, warned, or simply logged is a policy decision.

**How much of the tree an agent reads.** A task, its document, its links, its
children, its ancestors' documents — how much context is assembled per run is
the agent's business.

**Who approves what.** The model gives proposal tasks and `created_by`. Whether
every agent proposal needs approval, or only ones touching many nodes, is
policy.

**How an agent chooses what to do next.** The model offers reading order,
readiness, priority, and dependencies. Which of those an agent weighs, and how,
is not specified here.

**Conversation.** Where the chat between a person and an agent lives is not part
of this model. Conclusions from a conversation belong on the task, as a document
edit or a comment event. Transcripts belong wherever conversations already live.

---

## 7. The seams, as a checklist

If the implementation keeps these open, an agent can be added later without
changing the model.

```
   ① every derived value is available as data, not only rendered on screen
   ② a task can be created, filled in, and cascade-deleted cheaply, so a
     proposal can be reviewed and thrown away without a special draft state
   ③ created_by on every record can name an agent run, not only a person
   ④ every write can carry a run id, so a run can be undone as a range
   ⑤ declared scope (links) and observed scope (commits) can be compared
   ⑥ an agent's uncertainty lands as a typed event, not as a chat message
   ⑦ suggestions are always offered, never applied automatically
   ⑧ nothing an agent writes is a different shape from what a person writes
```

The eighth is the one that matters most. The moment an agent gets its own kind
of task, or its own kind of plan, there are two systems to keep in step, two
sets of screens, and a permanent question about which one is authoritative.

The next file, [13 — Flows](13-flows.md), walks through the ordinary situations
step by step, so the model can be checked against real usage.
