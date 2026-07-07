# 8 — Implementation checklist

Use this as a sprint-ready ordered list.

## Models and API

- [ ] Unify `RemoteAuth` / `RemoteConfig` with `versioning/remotes.py` (shared module, single shape for `remote_auth` dict).
- [ ] Extend `CreateProjectRequest` with optional `remote` + `remote_mode` (no separate clone DB id field).
- [ ] Add validation matrix: `remote` null vs set, mode enum; document **`remote_url`**: normal URL for `create_remote`, **full** URL (domain + remote DB) for `clone`.
- [ ] OpenAPI descriptions with examples for both URL shapes.

## Core logic

- [ ] Extract `bootstrap_empty_project_db(client, name, description) -> db_name` from current `ProjectRepo.create` (lines 57–71 area); keep `create` calling it + meta insert + `ProjectNode`.
- [ ] Implement remote client factory: given `remote_url` + auth, perform connection checks and return `AsyncClient` suitable for `create_database` / schema / insert on that server.
- [ ] **create_remote** path: remote bootstrap → local `ProjectSchema` → local `clonedb` → return `ProjectNode` for orchestrator.
- [ ] **clone** path: **only** local `clonedb` (no local `create_database` first) → local `ProjectSchema` → return `ProjectNode` for orchestrator.
- [ ] Clone mode: pass user’s **full** `remote_url` as `clone_source`; `newid` from `slugify(name)` with **clone-safe** id conflicts (409 or alternate `newid`, never empty local `create_database`).
- [ ] Create mode: implement helper to build **full** clone URL from normal base `remote_url` + `db_name` for Step 4 `clonedb`.

## Service / routes

- [ ] Add `ProjectService` methods (or equivalent) for the two remote flows; keep `project_routes.create_project` readable (< 30 lines of branching ideally — delegate to service).
- [ ] Resolve DI: `ProjectService` / `ProjectRepo` available during create without existing `ProjectNode`.

## Push / pull

- [ ] Smoke-test existing `POST .../push` and `pull` after each creation path; document any manual `remote add` steps.
- [ ] Optional: link from project README or API docs to `versioning/remotes` endpoints.

## Quality

- [ ] Add unit tests for validation and `bootstrap_empty_project_db` (mock client).
- [ ] Fix any inconsistent `DatabaseError` key usage (`api:error` vs `api.error`) while touching `project_repo` (optional hygiene).
- [ ] Log structured errors for remote failures without leaking secrets.

## Docs

- [ ] This folder — update if implementation choices differ (e.g. final field names).
- [ ] Changelog or user-facing “Creating a remote-backed project” short guide (only if you maintain user docs outside this plan).
