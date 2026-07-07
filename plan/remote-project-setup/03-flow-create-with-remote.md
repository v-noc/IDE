# 3 — Flow: create new project with remote bootstrap (`create_remote`)

**User intent:** New project name/description/path; they want the empty graph to exist on a **remote** first, then work locally in sync with that starting point.

## Preconditions

- `RemoteConfig` with valid **`remote_url` (normal server URL only)** and `auth`.
- Local path exists.
- Local Terminus can run `clonedb` from that remote (network, compatible versions).

## Step-by-step

### Step 1 — Choose `db_name`

Same as today: `slugify(name)`, handle `DatabaseAlreadyExists` on the **remote** with timestamp suffix (reuse logic from `project_repo.create`).

### Step 2 — Bootstrap empty graph on the remote

Using an `AsyncClient` (or cloned client) configured for the **normal** `remote_url` with the provided auth:

1. `create_database(db_name, ...)`
2. `ensure_schema(...)` with the same arguments as local create (schema label, description, team list)
3. Insert init `FolderSchema` document with the same commit message as today

This is the **same sequence** as lines 55–71 in `project_repo.py`, but executed against the remote connection, not the default local meta/project connection.

**Note:** Implementation detail — either construct a remote-scoped client from env pattern used elsewhere, or add a small factory `client_for_remote(url, auth)` that returns an `AsyncClient` with `_check_connection(check_db=False)` for admin operations. Keep this in one place for testing.

### Step 3 — Create global project registry on **local meta**

Using the **existing** local meta `AsyncClient` (same as current `create`):

1. Build `ProjectSchema` with `_id` / `db_name` matching Step 1, `name`, `description`, `local_path=path`.
2. `insert_document(project, commit_msg=...)`

No clone of `ProjectSchema` from remote — new document locally.

Optional MVP+ : persist `remote_url` (and optionally `default_remote = "origin"`) on `ProjectSchema` for UX; not required for correctness if auth is passed on every push/pull.

### Step 4 — Clone remote DB to **local** Terminus

Using the **local** admin client (same entrypoint as `remotes.clone_remote`):

1. Build **`clone_source`** as the **full** URL to the database you just created on the remote (domain + DB id / path segment Terminus expects). The user only supplied a **normal** base URL for Steps 1–2; the server composes the full clone URL from that base + `db_name` (or equivalent), following your Terminus deployment’s URL rules.
2. Call `clonedb(clone_source=full_clone_url, newid=db_name, description=..., remote_auth=auth_dict)`.

Do **not** call local `create_database` before this step: **`clonedb` creates the local DB** and aligns its history with the remote. (Same principle as [04-flow-clone-existing.md](./04-flow-clone-existing.md) — empty local create + clone diverges heads.)

Result: local Terminus now has a database `db_name` whose content matches the remote empty bootstrap.

### Step 5 — Build `ProjectNode` and run orchestration

Same as `project_routes.create_project` today:

1. Construct `ProjectNode` from the `ProjectSchema` fields.
2. `ProjectUoW(db, project_node, RequestDbContext(branch="main", ref=None))`
3. `GraphBuilderOrchestrator(...).resync()`
4. Build tree response

## Ordering summary

```text
Remote:  create_database → ensure_schema → init folder
Local meta:  insert ProjectSchema
Local data:  clonedb(remote → local db_name)
Local:  orchestrator.resync()
```

## Failure and rollback (MVP)

- If Step 2 succeeds but Step 3 fails: remote has an orphan DB; document manual cleanup or add a compensating `delete_database` on remote in a `finally` (nice-to-have).
- If Step 4 fails: meta has `ProjectSchema` but no local DB; return clear error; optional cleanup of meta doc (harder — may leave orphan meta row; simplest MVP is clear error + manual delete project).

Defer transactional saga to post-MVP unless quick wins exist.
