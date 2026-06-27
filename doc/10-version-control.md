# 10 · Version Control (TerminusDB)

V-NOC's graph is stored in **[TerminusDB](https://terminusdb.com/)**, an immutable, append-only graph database with **built-in Git-style version control**. That means *every change to the graph itself — code structure, logs, tests, playgrounds, documents — is a commit* on a branch, can be diffed against any other commit, and can be pushed or pulled from a remote.

This is not a layer V-NOC adds on top of TerminusDB. It is what TerminusDB does natively, and V-NOC exposes it through `/api/v1/versioning/*`.

---

## What this gets you

| Capability | TerminusDB primitive | V-NOC endpoint |
|---|---|---|
| Branch the graph | `branch` | `POST /api/v1/versioning/branches/` |
| List branches | `branch ls` | `GET /api/v1/versioning/branches/` |
| Delete a branch | `branch rm` | `DELETE /api/v1/versioning/branches/{name}` |
| Inspect history | `log` | `GET /api/v1/versioning/commits/` |
| Diff two commits | `diff` | `GET /api/v1/versioning/commits/diff?from=…&to=…` |
| Clone a remote | `clonedb` | `POST /api/v1/versioning/remotes/clone` |
| Push to a remote | `push` | `POST /api/v1/versioning/remotes/push` |
| Pull from a remote | `pull` | `POST /api/v1/versioning/remotes/pull` |
| Fetch from a remote | `fetch` | `POST /api/v1/versioning/remotes/fetch` |

Routes live under `src/backend/app/api/v1/versioning/`.

---

## Branches

Branches in V-NOC are **graph branches**, not git branches. They diverge from a commit, accumulate changes, and can be merged back. Use them to:

- **Experiment** with a refactor on a copy of the graph and discard the branch if you don't like it.
- **Hold different views** of the same project (e.g. "production analysis" vs "spike").
- **Isolate AI agent work** — let the agent operate on its own branch and review the diff before merging.

```bash
curl -X POST http://localhost:8000/api/v1/versioning/branches/ \
  -H 'Content-Type: application/json' \
  -d '{"name":"refactor-payments"}'
```

The active branch is part of the request context (see `RequestDbContext` in `src/backend/app/db/context.py`) so reads and writes during a session target the same branch.

---

## Commits

Every meaningful operation in V-NOC produces one or more TerminusDB commits. You can list them:

```bash
GET /api/v1/versioning/commits/?branch=main&limit=50
```

And diff them:

```bash
GET /api/v1/versioning/commits/diff?from=<commit-a>&to=<commit-b>
```

The diff is a structured graph diff — added/removed/changed nodes and edges — not a text diff. That's the point: you can ask "what *symbols* changed between these two states?" without inferring it from a code diff.

---

## Remotes

A TerminusDB remote is another TerminusDB instance you push to and pull from. V-NOC wraps the four standard operations:

| Op | Endpoint | When to use |
|---|---|---|
| `clone` | `POST /api/v1/versioning/remotes/clone` | Bring a remote graph onto this machine |
| `fetch` | `POST /api/v1/versioning/remotes/fetch` | Update the local copy of the remote's refs without merging |
| `pull` | `POST /api/v1/versioning/remotes/pull` | Fetch + fast-forward the local branch |
| `push` | `POST /api/v1/versioning/remotes/push` | Send local commits to the remote |

The remote credentials are typed in `src/backend/app/api/schemas/terminus_remote.py` (`RemoteConfig`).

### Remotes during project creation

You don't have to wait until after a project exists to set up a remote. `POST /api/v1/projects/` takes a `remote_mode` field:

| Mode | Meaning |
|---|---|
| `none` | Local only |
| `create_remote` | Create the project locally, then bootstrap it on the supplied remote URL |
| `clone` | Clone an existing graph from the remote into the local TerminusDB |

See `04-creating-a-project.md` for full request shapes.

---

## How V-NOC uses this internally

- **Project creation** commits the initial graph in a single transaction.
- **Watcher updates** batch file-level reparses into one commit per change burst (so an editor save isn't 50 commits).
- **Agents** are encouraged (UI-side) to work on a fresh branch.
- **Test runs**, **log ingest**, and **playground execution** each produce their own commits, which makes "what changed when this test started failing?" a graph diff.

The Terminus client wrappers live in `src/backend/app/db/`:

- `async_terminus_client.py` — async wrapper around the official client
- `client.py` — singleton + startup migration (`migrate_base`)
- `remote_terminus.py` — remote-specific helpers
- `terminus_client/` — lower-level WOQL utilities
- `context.py` — per-request db context (branch, ref, etc.)

---

## Why version control belongs in the database

If versioning were stored in a separate system, none of this would work:

- A graph diff would need a second store to walk.
- Branching the graph would need a custom snapshot system.
- Push/pull would be a bespoke sync protocol.

By using TerminusDB, V-NOC gets all of that **for free**, with the same guarantees as Git on text — but applied to the structured representation of your code.

---

## Operational notes

- Default TerminusDB URL: `http://localhost:6363` (`TERMINUS_PORT`).
- Default DB name: `v_noc` (`TERMINUS_DB`).
- Admin password must match `TERMINUS_KEY` (`TERMINUSDB_ADMIN_PASS`). See `03-getting-started.md`.
- Volumes are persisted to a Docker named volume `terminusdb_storage`. Wipe with `make reset-db`.

Next: [11 · Makefile Reference](11-makefile-reference.md).
