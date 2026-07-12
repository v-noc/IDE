# Phase 4 / Step 4 — Verification

## Structural gates (CI)

- `BaseRepo` file deleted; no `from app.core.repository.base_repo import`.
- `commit_msg=` only in `write_batch.py` + `migration/`.
- `print(` absent from `app/core`, `app/api`, `app/db`.
- `raw=True` absent from `app/core/services`.
- Import-linter (or a simple AST test) enforcing layering:
  `api → services → repository → db`; `services` may not import `db.async_terminus_client`.

## Behavior tests

1. Full suites green: `tests/unit/service/`, `tests/unit/parser/`, `tests/e2e/` —
   the phase is behavior-preserving except error surfaces.
2. Error surfaces (new):
   - kill TerminusDB → `GET children` returns 502 JSON error (not `[]`/200).
   - `register_logs_batch` with DB down → JSON-RPC error object (not `ok: true`).
   - update on readonly UoW (ref set) → 409.
3. Group deletion re-parents to logical parent for all three families
   (extend `tests/unit/service/group/*`).
4. If code_position flattening ships: migration test — old-schema fixture DB →
   migrate → golden graph equal; UI position rendering e2e spot-check.

## Review checklist per converted service

- [ ] one commit per public method (commit-count fixture from Phase 2)
- [ ] no dict-shaped returns
- [ ] raises typed errors; route translates
- [ ] unit test exercises staging without a live DB (batch is inspectable)
