# 4 — Flow: clone existing remote database (`clone`)

**User intent:** A database already exists on the remote. They provide **project metadata** (name, description, path) and a **full** remote clone URL; V-NOC does not run `create_database` + `ensure_schema` on the remote — only `clonedb` locally, then the global project registry and orchestration.

## Critical: do not create the local DB before `clonedb`

On **clone**, the local project database must **not** be created with `create_database` (or any empty bootstrap) before `clonedb`.

- `create_database` on local creates its **own** initial commit / head on an empty DB.
- `clonedb` is what **creates** the local database **and** copies the remote’s commit history into it.

If you create an empty local DB first and then clone (or mix the two), histories **diverge** — you no longer have a straight copy of the remote head. The only local data-plane step for clone is **`clonedb`** (plus later orchestration commits on top of that clone).

## Preconditions

- `RemoteConfig` with **`remote_url` = full URL** (domain **and** remote database id in the form Terminus expects for `clone_source`) plus `auth`.
- Local path exists.

## What we ask the user for (MVP)

| Input | Why |
|-------|-----|
| `name`, `description`, `path` | Build `ProjectSchema` / `ProjectNode` and orchestration root. |
| Full `remote_url` | Single string that identifies server **and** the remote DB to clone. |
| `auth` | `clonedb` remote authorization. |

We do **not** require a separate `source_db_id` field — it is implied by the full URL. We do **not** require a full `ProjectSchema` JSON — we **reconstruct** it locally from the form fields + resolved local `db_name`.

## Local `newid` / `db_name` (decided)

Pick the local database id from the **project `name`** via `slugify(name)`, same *naming* convention as local-only `create`.

**Collision handling differs from `project_repo.create`:** today `create` fixes collisions by calling `create_database` again with a suffixed id. For **clone** you must **not** do that — never create an empty DB to “reserve” a name. If `slugify(name)` is already in use as a local DB id, either return **409** or choose an unused `newid` (e.g. append timestamp) and call **`clonedb` once** with that `newid` so Terminus still creates the DB only via clone.

That final `newid` is both `clonedb`’s `newid` and `ProjectSchema.db_name`.

The remote DB’s name (inside the full URL) does **not** need to match local `db_name`.

## Step-by-step

### Step 1 — `clonedb` on local Terminus

Call local client `clonedb`:

- `clone_source`: the user-provided **full** `remote_url` (domain + remote DB id)
- `newid`: local `db_name` (slugify + **clone-safe** collision rule above — **not** the `create_database`-then-retry pattern)
- `description`: user description or default
- `remote_auth`: from request

`clonedb` **creates** the local DB and imports the remote history. Do **not** run local `create_database` / `ensure_schema` / init folder before this step.

### Step 2 — Create `ProjectSchema` on local meta

Insert a **new** document:

- `db_name` = `newid` from Step 1
- `name`, `description`, `local_path` from request
- `_id` convention: can match `db_name` as today for consistency with `get_by_id`

### Step 3 — Build `ProjectNode`, orchestrate

Identical to normal create: `ProjectUoW` scoped to `db_name`, `GraphBuilderOrchestrator.resync()`.

**Note:** After a pure clone of an already-analyzed project, `resync` may be a no-op or incremental depending on orchestrator logic — that is existing behavior, not remote-specific.

## Ordering summary

```text
Local data:  clonedb(full remote URL → local db_name)
Local meta:  insert ProjectSchema (new, links to db_name)
Local:  orchestrator.resync()
```

## Edge cases

- **Local DB id already exists**: If chosen `newid` is already a database on local Terminus, do **not** create an empty DB; pick another unused `newid` or return 409, then single `clonedb` call.
- **Meta collision**: If `ProjectSchema` `_id` or `db_name` collides with an existing local project registry row, return 409 with a clear message.
- **Clone auth failure**: Surface remote error; do not create `ProjectSchema`.
- **Partial failure**: If `clonedb` succeeds but meta insert fails, local has a DB without registry — document cleanup (delete database + retry) or add compensating delete (post-MVP polish).
