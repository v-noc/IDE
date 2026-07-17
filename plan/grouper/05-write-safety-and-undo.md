# Grouper 05 — Write Safety, Origin, Undo

The grouper's safety story is structurally simpler than describe/document's
(agent-v3 shared/03) because of README decision 1: **the run is read-only
until gate 2 approves.** There is no mid-run partial write to be truthful
about — before approve, cancel costs nothing; after approve, exactly one
batch exists to undo.

## The write (`commit()`, 03's second handler)

Approved proposal in, groups out — through the **same service the human path
uses** (`GroupService`, the engine behind `api/v1/group_routes.py`):

```python
for group in proposal.groups:                      # deterministic order
    await group_service.create(
        group.name,
        group.description,                         # the proposal's sentence
        parent_node_id=args.node_id,
        children=[(m.id, m.type) for m in group.members],
        group_type=partition_kind,                 # structure_group | code_element_group | call_group
    )
```

- `regroup=true` runs the dissolutions **first** (delete the marked
  agent-origin groups via the service — their members were already in the
  roster, 01), then the creations. One logical batch, dissolve-then-create,
  so a crash can't leave a child in two groups.
- Every commit id the batch produces is appended to the run artifact's
  `written_commits` (the agent-v3 field, same name, same purpose) plus
  `written_group_ids` — the undo needs both.
- No LLM calls in `commit()`. The write is deterministic replay of an
  approved document; if it can fail, it fails on graph state, not on model
  whim.

## Where the explanation lives (the user asked for this explicitly)

- **Per group**: `description` = the proposal's one-sentence "what unites the
  members" — already a field on every group (`GroupService.create` requires
  it); NodeCards and future rosters read it like any description.
- **Per run**: `dimension` (as approved/edited) + `edited_by_user` on the
  `group_proposal` artifact and in the tool result — the transcript answers
  "why is it grouped this way" forever, and the done card shows it.
- **Origin**: agent-written groups carry the agent-origin tag — the same
  mechanism agent-v3 shared/03 establishes for descriptions/docs, applied to
  the group doc type. (If the group schema lacks the field, adding it is part
  of G4 — it is the load-bearing bit that makes `regroup` and undo safe to
  scope to agent work only.) Human-drawn groups never carry it; nothing in
  this plan can delete a human group.

## Undo (G4)

Same shape as agent-v3's run-level undo, cheaper because the batch is one
moment:

- **Undo this run** (DoneView, behind the AlertDialog: "removes the 3 groups
  this run created; the children return directly under `payments/`; groups
  you've edited since are left alone and listed").
- Mechanism: revert the `written_commits` range. Per-group conflict rule: a
  created group whose membership or name changed *after* the run (user
  dragged children in/out on canvas, renamed the box) is **skipped and
  listed** — the user's later work outranks the undo, exactly the
  edited-since rule from agent-v3 shared/03.
- `regroup` runs: undo restores what the revert restores — the dissolved
  agent groups come back with the batch's revert (dissolve and create sit in
  the same commit range). This is why dissolution happens inside the batch
  and not as a separate earlier commit.
- The artifact flips to `reverted`; the done card dims with the `reverted`
  badge; the checklist-style record of what was skipped renders on the card.
  A reverted run's groups can be re-proposed by simply running the tool
  again — undo never blocks redo.

## Idempotence and re-runs

- Re-run over the same parent with everything still grouped →
  the 01 refusal ("already grouped — say 'regroup'"). The tool never
  silently stacks a second layer of groups.
- Re-run after a partial manual cleanup (user dissolved one box) → the freed
  children are simply in the pool again; agent groups still standing are
  excluded (or dissolved under `regroup`). No special cases: the pool
  definition (01) already answers every mixed state.
- Two conversations racing the same parent: the second `commit()` hits
  changed graph state; per 03's edge-case table, re-validation or the write
  itself fails with the honest sentence. Rare, boring, recoverable.

## Evals to watch after G4 (safety-specific)

- undo skip rate (high = users edit groups fast; consider shortening the
  window between approve and canvas exposure — or celebrate, since edits
  mean adoption);
- refusal rates per rule (a noisy "already grouped" refusal means the agent
  suggests the tool too eagerly — prompt the orchestrator, not the tool);
- zero tolerance: any human-origin group mutated by any grouper path is a
  release blocker, and the test suite pins it (fixture: parent with one
  human group + regroup run → group byte-identical after).
