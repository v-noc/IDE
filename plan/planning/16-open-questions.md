# 16 — Open Questions

Everything below was left unsettled on purpose. Each one is a real question,
each has options, and each has a lean, but none of them needs an answer before
the model can be built. Deciding them now would mean guessing, and a guess
written into a design document is harder to change than an open question.

---

## 1. Who is doing the work

There is no assignee field anywhere in this design.

**Options.** A single owner per task. A set of participants. Nothing at all,
letting the notes carry it.

**Lean: a single owner, added later.** Everything in the model works without it,
and adding one field later is easy. What matters more is that when it arrives,
an owner must be able to be **an agent run as well as a person**, because
otherwise there will be two parallel notions of who is doing something.

The question that actually needs thinking is not the field. It is what the
board does with it: filtering by owner is obvious, but "my work" across a
recursive tree is not, since somebody may own a parent while other people own
its children.

---

## 2. Estimates and dates

Also absent. No points, no hours, no due dates.

**Lean: stay out of it for now.** Estimation brings its own opinions, its own
arguments, and its own screens, and nothing in this design needs it. The one
thing worth noting is that a recursive tree makes rollup estimates tempting and
misleading, since a parent's estimate and the sum of its children's estimates
will disagree constantly and neither is wrong.

---

## 3. Whether work follows the branch or the project

Today's tasks live on the working branch, so a branch has its own view of the
work and promoting a branch merges the work with everything else.

**Options.** Keep it per branch. Pin work to one branch so it is
project-global. Split the difference, with tasks global and plans per branch.

**Lean: keep it per branch until somebody actually gets hurt by it.** The
model does not change either way; only the scoping does. The third option is
tempting and should be resisted, because "the task is here but its plan is on
another branch" is the kind of split that produces bugs nobody can reproduce.

---

## 4. Whether draft versions should take part in conflict detection

Right now they do not. A draft is a thought, and its links collide with
nothing.

**The argument for including them.** Two people writing two drafts over the same
class would like to know about each other early, and early is the whole point.

**The argument against.** Alternatives written by one person would fight with
each other on screen, and a person exploring three approaches would see three
conflicts that do not exist.

**Lean: keep drafts out, but consider a narrow exception** where a draft
conflicts only with **active** versions of **other** tasks, never with drafts
and never within the same task. That covers the useful case without the noise.

---

## 5. Whether a declared scope is enforced

The model records what a task says it will touch, and afterwards the commits say
what it did.

**Options.** Report only. Warn while working. Block an agent from touching
undeclared nodes.

**Lean: report first, warn second, never block in the first version.** Blocking
requires the declared scope to be right, and it will not be right until people
have been writing links for a while. A blocked agent that is right to want the
node produces exactly the frustration that makes people abandon a tool.

---

## 6. How deep is too deep

The design says most trees are two or three levels and does not enforce it.
Traversals have a ceiling so counts stay honest.

**Open: what the ceiling actually is**, and whether the interface should push
back when somebody creates a fourth or fifth level.

**Lean: a generous ceiling for correctness, and a gentle nudge in the interface
at the point of creation** rather than a refusal. The nudge should say what to
do instead, which is usually "put this detail in the document".

---

## 7. What happens to orphans over time

Orphans appear at the root level, which is right when there are five of them and
tiring when there are eighty.

**Options.** A filter. An archive state. Automatic cleanup after some period.

**Lean: a filter now, an archive state only if the filter proves insufficient.**
Automatic cleanup is ruled out. Deleting work because it fell out of a plan is
the one behaviour this design refuses everywhere else, and making an exception
here would undermine the reason people trust the rest.

---

## 8. Several boards, and sprints

One board, one set of columns, and a backlog column. No sprints, no
milestones.

**Lean: leave it.** The level board already gives a natural way to work on one
area at a time, which is most of what a second board would provide. Sprints are
a scheduling concept, and scheduling has not been designed here at all.

---

## 9. Whether progress should count deep by default

A parent can show progress over its direct children, or over everything
underneath it. The design defaults to direct, with a deep count available.

**The tension.** Direct matches what you see on the board level, which makes it
easy to trust. Deep matches what people mean when they ask how far along
something is.

**Lean: keep direct as the default and label the deep number clearly wherever it
appears.** The failure mode to avoid is two numbers that look the same and mean
different things.

---

## 10. Line-level links

Every link points at a node, so two tasks changing different parts of the same
large function are reported as a conflict when they might be fine.

**Options.** Leave it. Add an optional line range to a link. Rely on the
`accepted` decision to quieten false alarms.

**Lean: leave it, and rely on `accepted`.** Line ranges rot faster than anything
else in a codebase, and a stale line range would make the conflict detector
worse rather than better. If large functions turn out to be the main source of
false alarms, that is also useful information about the codebase.

---

## 11. Whether a dependency ever needs to point at a version

The design says dependencies point at tasks, because a version can be replaced
at any moment and a pointer into one breaks exactly when it is needed.

**The case that keeps coming back.** Somebody wants to record "I am waiting for
the specific thing described in the third step of their current approach".

**Lean: keep pointing at tasks, and let the node links carry the precision.**
The reason is already recorded on both sides: one task needs a node, the other
creates it. If that turns out not to be enough in practice, the smallest
addition would be an optional note on the dependency saying what is being
waited for, which is text and cannot rot into a broken reference.

---

## 12. How much an agent should fill in automatically

An agent proposing a version could add links by reading the code, and it would
usually be right.

**The risk.** Links are what everything else derives from. An agent that adds
forty links, three of which are wrong, produces confident wrong readiness and
confident wrong conflicts, and nobody will audit forty rows.

**Lean: agents propose links inside a draft version, and a person activating
that version is the approval.** That way approval happens once, at a moment
somebody is already reading, rather than forty times.

---

## 13. Where conversation lives

Chat between a person and an agent about a task is not part of this model.

**Lean: keep it out, and make the conclusion land on the task.** A decision
reached in a conversation belongs in the document or in a note, where somebody
can find it. Transcripts belong wherever conversations already live in the
product.

---

## What is deliberately closed

To be clear about which arguments are finished, these are settled and should not
be reopened without new evidence:

```
   one entity type. work is recursive.
   a version refers to children; it never owns them.
   dependencies connect tasks, never versions or list positions.
   position in a list is advice and never blocks anything.
   the graph has five node kinds; a field is a sentence, not a node.
   derived values are never stored.
   a conflict is computed; only the human decision about it is stored.
   nothing deletes somebody's work as a side effect of anything.
```

---

The worked example is next: [examples/social-media](examples/social-media/) runs
every part of this design over a small application, from an empty board to
finished work.
