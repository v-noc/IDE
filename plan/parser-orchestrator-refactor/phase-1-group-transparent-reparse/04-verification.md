# Phase 1 / Step 4 — Verification

## Invariant to prove

> Resync of an unchanged project with groups at every level produces an empty ChangeSet
> (no moves, no modifies) and therefore **zero commits**.

## Unit tests (no DB — resolver + policy)

New: `tests/unit/parser/analyzer/hierarchy/test_group_resolver.py`

| Case | Setup (synthetic edges) | Expect |
|---|---|---|
| flat group | folder→SG→file | logical(file)=folder, owning_group=SG |
| nested groups | folder→SG1→SG2→file | logical(file)=folder, owning_group=SG2 |
| root group | project-root→SG→folder | logical(folder)=root |
| cycle | SG1→SG2→SG1→file | logical=None, warning logged, no crash |
| ungrouped | folder→file | logical=folder, owning_group=None |

New: `tests/unit/parser/analyzer/hierarchy/test_move_policy.py`

| Case | desired vs logical | Expect |
|---|---|---|
| grouped, unmoved | equal | no move |
| grouped, real FS move | differ | move to new logical parent; `old_group_id` set |
| ungrouped rename same dir | equal | no move (modified only) |

## Change-detector tests (extend existing)

`tests/unit/parser/analyzer/hierarchy/test_change_detector.py` — add:

1. **grouped file, no disk change** → ChangeSet empty.
2. **grouped folder, no disk change** → ChangeSet empty.
3. **grouped file modified in place** → exactly one `modified`, zero `moved`,
   group edge untouched after sync.
4. **grouped file moved on disk** → exactly one `moved` with
   `new_parent_id = new folder`, `old_group_id = SG`.
5. **parent folder renamed** → children `modified` (path), zero `moved`.

## AST-processor tests

Extend `tests/unit/parser/analyzer/class/test_class_sync.py` (or add
`test_code_element_group_sync.py`):

1. method inside CodeElementGroup under class → re-sync file unchanged → no moves,
   group intact, no deletes.
2. grouped top-level function → same.
3. class deleted from source, its group orphaned → group deleted in same batch.

## E2E (uses existing harness `tests/e2e/core/group/`)

Extend `test_structre_group.py` / `test_code_element_group.py`:

```
create project → sync → create groups via API (structure root, structure nested,
code-element on file, code-element under class, call group)
→ POST resync → assert group children unchanged
→ POST resync again → assert commit log gained ZERO commits (query TerminusDB
  commit history via versioning API before/after)
→ touch one file (whitespace) → resync → assert only that file's content commit,
  groups intact
```

The commit-count assertion doubles as the Phase 2 baseline metric.

## Manual smoke

1. Run app, create groups in UI, hit resync button twice, drag-check groups.
2. `git log`-style commit view (versioning UI) — confirm no "Moving items" commits
   appear after resyncs.
