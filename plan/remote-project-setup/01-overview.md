# 1 — Overview

## Goal

Let users optionally tie a V-NOC project to a **TerminusDB remote** during creation, in one of two ways:

1. **Create (remote-first)** — User is starting fresh but wants the canonical empty graph to live on a remote first, then have a matching local copy and run the usual code-analysis orchestration on the **local** database.
2. **Clone** — User already has a project database on a remote (or a teammate pushed one). They provide metadata; **`clonedb` alone creates the local DB** (no prior local `create_database`, which would diverge heads). Then insert the global **project registry** document and run orchestration on local.

Both paths end in the same steady state: a `ProjectNode` / `ProjectSchema` in the **meta** (global) store, a **per-project** database id (`db_name`) on the local Terminus instance with graph content aligned to the remote for the initial snapshot, and the existing `GraphBuilderOrchestrator` run against the local project DB.

## MVP principles

- **Simple**: No mandatory persistence of remote URLs or credentials on the server beyond what we already store in `ProjectSchema` if we choose to add fields later. For MVP, remote URL and auth can be supplied when needed (create + each push/pull).
- **Explicit auth on push/pull**: Users pass `RemoteAuth` (or equivalent) on each push/pull request, matching the existing pattern in `versioning/remotes.py`.
- **Open for growth**: Optional fields on `ProjectSchema` for `remote_url` / `default_remote` name can be added later without changing the core flows.

## Terminology

| Term | Meaning |
|------|---------|
| **Meta client** | The default `AsyncClient` from `get_terminus_client` — holds global documents such as `ProjectSchema`. |
| **Project DB** | The database named `db_name` on the local Terminus server; holds folders, files, code graph, etc. |
| **Remote** | Another TerminusDB endpoint (URL) used for `clonedb`, `push`, `pull`. |

## `remote_url` shape (by mode)

The same field name `remote_url` (inside `RemoteConfig`) carries **different** expectations:

| `remote_mode` | What the user supplies |
|---------------|-------------------------|
| **`create_remote`** | A **normal** server URL — e.g. origin / API base for the remote Terminus instance **without** embedding a specific database id in the path. Used to open a client, run `create_database`, `ensure_schema`, and init folder on that server. |
| **`clone`** | A **full** URL including **domain and remote database id** (whatever single string Terminus expects as `clone_source` for that DB). No separate `source_db_id` field in the API. |

For **`create_remote`**, the follow-up local `clonedb` still needs a full clone URL for the DB that was just created; the backend **derives** that from the normal base URL plus the chosen `db_name` (per Terminus URL rules), not from the user.

## Important invariant

**`ProjectSchema` is not cloned from the remote.** It lives only in the meta store. For both flows we **create a new** `ProjectSchema` document locally that points at the correct `db_name` (and optional remote metadata later). The remote only carries the **project database** payload (schema + data commits), not the global project registry document.

**Local `db_name` / `clonedb` `newid`** follows the **project name** rule (`slugify(name)`), with id collisions resolved **without** calling local `create_database` first in **clone** mode (see [04-flow-clone-existing.md](./04-flow-clone-existing.md)). The remote database identity lives in the **clone** full URL and does not need to match the local `db_name`.

## What “same as current `create`” means for the DB

The block in `project_repo.create` (slugify → `create_database` → `ensure_schema` → init `FolderSchema` → then meta `insert_document`) is the **template** for bootstrapping an empty project graph. For remote-first creation, that sequence runs **against the remote** (using credentials) so the remote is the source of truth for the initial empty graph; then we clone that DB to local so local matches remote before orchestration adds code-derived nodes.
