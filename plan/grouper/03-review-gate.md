# Grouper 03 — The Review Gate (Second Confirmation)

v2's harness pauses a tool once: estimate → `interrupt()` → decision → run
(harness/03). The grouper needs a second pause *after* the model has worked
but *before* anything is written — and the user's decision this time carries
**edits**, not just knobs. This doc designs that gate as harness machinery,
because the grouper won't be the last tool to want it (document outlines,
future refactor plans — anything proposal-shaped).

## The seam: `ToolSpec.review`

```python
class ToolSpec:
    …
    confirmation: Literal["always", "never"] = "always"   # gate 1 (exists)
    review: Literal["always", "never"] = "never"          # gate 2 (new)
```

`review="never"` tools behave exactly as today — the field's default makes
this change invisible to walkthrough/describe/document. `review="always"`
means: after the tool's proposal phase, the harness interrupts again and the
run only proceeds with an approved (possibly edited) proposal.

**Shape of the tool-side contract.** A reviewing tool splits its handler:

```python
async def propose(args, services) -> Proposal        # read-only, spends LLM calls
async def commit(args, proposal, services) -> ToolOutcome   # writes, no LLM
```

Non-reviewing tools keep their single `run()`. The harness owns the pause
between the two — the tool never sees interrupt mechanics, same division of
labor as gate 1.

## Wire model

**New tool part state**, between `running` and `completed`:

```
pending → awaiting_confirmation → running → awaiting_review → running → completed
                                                            ↘ cancelled
```

`awaiting_review` carries the proposal *reference*, not the proposal body —
the body lives on the mirror like every other big payload:

- **Proposal doc**: `group_proposal/<run_id>`, opened on the multi-doc stream
  when the proposal validates (patcher v2, nothing new). Snapshot =
  `GroupProposal` + the roster echo (id → name/kind, so the frontend renders
  chips without a second fetch) + the knobs. Reload-safe by construction —
  same mirror/`getArtifact` path as walkthrough and checklist docs.
- The part's state payload: `{"status": "awaiting_review",
  "proposal_doc": "group_proposal/<run_id>"}`.

**Decision endpoint** (the existing one, payload extended — not a new route):

```json
POST …/decision
{ "kind": "review",
  "action": "approve" | "cancel",
  "proposal": { …edited GroupProposal… }     // required on approve
}
```

Gate-1 decisions keep their current shape (`kind: "confirmation"` implied /
defaulted) — the endpoint dispatches on `kind`, old clients unaffected.

## Resume semantics (LangGraph, nothing hand-rolled)

Gate 2 is a second `interrupt()` inside the same tool node — LangGraph
supports repeated interrupts per thread; the checkpointer (thread_id =
conversation_id) already persists across them. Resume feeds the decision
back in; the harness:

1. `action == "cancel"` → part state `cancelled`, proposal doc closed with
   status `cancelled`, turn continues (the agent gets
   `{"status": "cancelled_at_review"}` and says so in one line).
2. `action == "approve"` → **re-validate the submitted proposal** with the
   same validator that judged the model (02) against the same roster and
   knobs. The frontend mirrors the rules for live feedback, but its verdict
   is advisory — the backend's is real. Invalid edit → the decision is
   rejected (HTTP 422 with the validator sentences), the part **stays**
   `awaiting_review`, the card shows the errors inline; the run is not dead.
3. Valid → `commit()` runs (writes, 05), part → `running` (label "writing
   groups…") → `completed`. The *approved* proposal is patched onto the
   proposal doc, `edited_by_user` computed by diff and stamped on it — the
   transcript records what the user changed, which is eval food (02).

## Edge cases, decided

| Case | Behavior |
|---|---|
| user walks away at gate 2 | same as gate 1's answer: the interrupt is checkpointed; the card renders `awaiting review` on reload indefinitely. No timeout in v1 — a pending proposal writes nothing and costs nothing. |
| user sends a new message while a review is pending | same rule as gate 1 pending confirmations (harness/03): the pending run must be resolved first; the composer surfaces "a proposal is waiting for review" — one active run per conversation, unchanged. |
| roster changed under the proposal (parser re-ran, a child was deleted between propose and approve) | re-validation catches it: unknown ids fail the exactly-once law; the 422 message says "the tree changed — cancel and re-run". Cheap, honest, rare. |
| approve payload omits `proposal` | 422; approve always carries the full proposal (edited or verbatim) — no "approve whatever the server has" ambiguity between two caches. |
| tool errors during `commit()` (write fails mid-batch) | part → `error`; whatever the batch wrote is in `written_commits` and the undo path (05) applies; the proposal doc records `status: "error"`. |

## Why not "write then let the user edit on canvas"

Rejected alternative, for the record: skip gate 2, write immediately, tell
the user to fix boxes by hand. It reuses zero-new machinery — and it's
wrong: it turns every mediocre proposal into cleanup work, makes "cancel"
mean "manually delete N groups", and teaches users to fear running the tool.
The review gate is the difference between a tool that *suggests structure*
and one that *litters*. Worth one spec field, one part state, one decision
kind.

## Cost of the seam (kept small on purpose)

Harness: one `ToolSpec` field · one part state in the union · one decision
`kind` branch · the propose/commit split for reviewing tools. Frontend: one
badge variant + one face slot (04). Everything else — interrupts,
checkpointing, mirror docs, decision route — already exists. If this list
grows during implementation, the seam is being over-built; stop and re-read
this page.
