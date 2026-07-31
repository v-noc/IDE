# Shared 03 — Write Safety and Undo

v3 tools are the first agent code that mutates the graph. Three layers of
safety, each independent: provenance on every write, overwrite rules that
protect human text structurally, and run-level undo built on what TerminusDB
already gives us.

## Layer 1 — provenance: every write says who wrote it

```python
description_meta / doc_meta = {
    "origin": "agent",
    "run_id": …,               # → the ToolRun artifact, which has everything else
    "prompt_version": …,
    "model_id": …,
    "commit_id": …,            # the commit the CONTENT was generated against
}
```

**Why.** Overwrite rules (layer 2) need to distinguish human text from agent
text *reliably* — a heuristic ("looks generated") would eventually delete
someone's hand-written doc. Absence of `origin: "agent"` means human; that's the
whole test. Provenance also makes staleness checkable later
(`meta.commit_id != head` — the future sweep tool) and attributes quality
regressions to a prompt version.

## Layer 2 — overwrite semantics (identical for both tools)

| Existing text on the node | `overwrite=False` (default) | `overwrite=True` |
|---|---|---|
| none | write | write |
| agent-origin | **skip** (`skipped_existing`) | replace |
| human-authored | **skip** | **still skip** — no flag reaches human text |

- `overwrite=True` flips the tool's confirmation policy to **always** (v2's
  `ToolSpec.confirmation` already supports this) — replacing 30 descriptions is
  never an auto-run, whatever the estimate says.
- Documents don't pile up: a re-run **replaces the node's previous agent-origin
  doc** (matched by `doc_meta.origin` + tool) instead of appending generation
  after generation. Human docs on the same node are untouched, always.

**Why human text is unreachable even with the flag.** A flag is one careless
click; deleting a colleague's writing must require deliberately editing that
node, not batch-running a tool. This rule is structural (the repo method
refuses), not prompt-level.

## Layer 3 — undo, the TerminusDB way

Claude Code and Cursor built checkpoint/rewind systems on file snapshots, with
real pain. We get the same feature nearly free: **every graph write is already a
TerminusDB commit** (the repo layer commits per update with a message). The run
just has to remember its commits:

- during the run, every write appends its commit id to
  `ToolRun.written_commits` (recording is free — the repo returns it);
- `POST /conversations/{cid}/runs/{run_id}/revert` walks `written_commits` in
  reverse and applies each commit's **inverse diff** (TerminusDB's diff/patch
  API — same family the versioning routes already use);
- the run's status becomes `reverted`; the checklist shows it; the revert itself
  is commits too, so undo is auditable and even re-doable.

Decisions inside that design:

- **Undo is per-run, not per-item.** "Undo item 14 of a describe run" invites
  inconsistent states (a parent summarized from a child description that was
  reverted). The run is the transaction the user reasoned about at the confirm
  card; it's the unit they get back.
- **Revert refuses if a node was edited by someone else after the run** (its
  current text ≠ what the run wrote — cheap check against the recorded write).
  Those nodes are listed and left alone; the rest revert. Silent clobbering of
  newer edits would make undo scarier than no undo.
- **Recording ships in Phase A; the revert endpoint ships in Phase C.**
  Recording costs one list append and cannot be retrofitted onto past runs —
  so it starts on day one even though the button comes later. *(Verify on
  install: the python client's diff/patch surface for inverse application —
  same "verify on install" honesty as the WOQL `{n,m}` probe.)*

## Idempotency (the boring guarantee that makes re-runs safe)

Re-running after a crash is always the answer, for both tools: default
`overwrite=False` means already-written nodes skip, and the run picks up exactly
the holes — the post-order property (shared/01) guarantees no half-written
dependencies. A re-run is a new ToolRun artifact; runs are never mutated after
they close.
