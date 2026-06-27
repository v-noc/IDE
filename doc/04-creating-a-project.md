# 04 · Creating a Project

V-NOC is a **web-based IDE that operates on local source trees**. Because the frontend runs in a browser, it cannot pick a folder for you via "File → Open". You tell the backend where your code lives by passing an **absolute path** on the machine running the backend.

This page covers:

1. The three project modes (local, remote bootstrap, clone)
2. The request shape and where to send it
3. What V-NOC does after the project is created
4. How to delete or re-create a project safely

---

## The path you supply

The `path` field is an **absolute filesystem path** on the **host running the backend**. Examples:

- macOS / Linux: `/Users/me/code/my-app`
- Linux server: `/srv/projects/my-app`
- Windows (if the backend runs there): `C:\\Users\\me\\code\\my-app`

> [!IMPORTANT]
> If you're running the backend in Docker or on a remote machine, the path must exist **inside that environment**, not on your laptop. Mount your code into the container or run the backend natively.

The backend refuses the request if the path doesn't exist (unless you're cloning from a remote — see below).

---

## The three modes

The `remote_mode` field on the create request decides what V-NOC does with the source and with TerminusDB:

| Mode | What it does | When to use |
|---|---|---|
| `none` | Local-only project. The graph lives in your local TerminusDB. No remote. | Personal projects, quick exploration |
| `create_remote` | Creates the graph **locally**, then bootstraps it on a remote TerminusDB URL you provide. Subsequent commits can be pushed. | Sharing a graph across machines / teammates |
| `clone` | Clones a graph from a remote TerminusDB URL into your local TerminusDB. The local `path` is where V-NOC will check the source out / look for it. | Joining an existing V-NOC project |

The `remote` field is required for `create_remote` and `clone`. It carries the Terminus URL and credentials.

---

## Creating from the UI

In the frontend, open **New Project** and fill in:

| Field | Required | Notes |
|---|---|---|
| Name | ✓ | Display name, ≥ 3 characters |
| Description | — | Free text |
| Path | ✓ | Absolute path on the backend host |
| Remote mode | ✓ | `none` / `create_remote` / `clone` |
| Remote URL + credentials | only if remote mode ≠ `none` | TerminusDB endpoint |

Hit **Create**. The canvas opens with the project's graph as it materialises.

---

## Creating from the API

### Local project

```bash
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H 'Content-Type: application/json' \
  -d '{
        "name": "my-app",
        "description": "Internal billing service",
        "path": "/Users/me/code/my-app",
        "remote_mode": "none"
      }'
```

### Local + create remote

```bash
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H 'Content-Type: application/json' \
  -d '{
        "name": "my-app",
        "path": "/Users/me/code/my-app",
        "remote_mode": "create_remote",
        "remote": {
          "url": "https://terminus.example.com",
          "team": "my-team",
          "user": "me",
          "key": "***"
        }
      }'
```

### Clone an existing graph

```bash
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H 'Content-Type: application/json' \
  -d '{
        "name": "my-app",
        "path": "/Users/me/code/my-app",
        "remote_mode": "clone",
        "remote": {
          "url": "https://terminus.example.com/my-team/my-app",
          "team": "my-team",
          "user": "me",
          "key": "***"
        }
      }'
```

For `clone`, V-NOC pulls the graph from the remote first, then expects the source to either already exist at `path` or to be checked out there afterwards (e.g. via `git clone` from your source remote).

---

## What happens after `POST /projects/`

The orchestrator (`GraphBuilderOrchestrator`) runs a deterministic pipeline:

1. **Persist** a `ProjectNode` in TerminusDB.
2. **Walk** the project directory, skipping ignored paths (e.g. `node_modules`, `.venv`, build folders).
3. **Parse** each supported source file by dispatching to the matching **language driver** (see `05-language-drivers.md`).
4. **Inject stable IDs** into the source as docstring/comment markers — `""" ID: <uuid> """` for Python — so symbols keep their identity across renames and refactors. See `06-function-class-tracking.md`.
5. **Resolve calls and MRO** by asking the driver for cross-references.
6. **Insert** nodes (files, folders, functions, classes) and edges (imports, calls, inheritance) into TerminusDB.
7. **Start a watcher** that re-parses files on save and emits Socket.IO deltas to the canvas.

Progress is streamed live to the frontend, so large projects show their graph filling in node-by-node.

---

## Re-parsing, syncing, and deletion

| Action | How |
|---|---|
| Re-parse a single file | Just save it — the watcher picks it up |
| Force a full re-walk | Re-create the project (delete + create), or trigger the re-parse endpoint |
| Delete a project | `DELETE /api/v1/projects/{id}` — removes graph nodes & stops the watcher. The source on disk is untouched |
| Inspect projects | `GET /api/v1/projects/` |

> [!NOTE]
> `vector_storage/` (the Vectorlink data dir) lives in `src/backend/`. Deleting a project does **not** delete the embeddings; that is handled separately.

---

## Tips for healthy projects

- **Use an ignore-aware path.** Point at the project root, not at `node_modules`.
- **Pick languages V-NOC supports.** Today: Python, TypeScript, JavaScript. Other files are stored as opaque file nodes.
- **Keep the path stable.** If you move the directory, recreate the project — file nodes are keyed by path.
- **Run the backend natively when possible.** Docker-in-Docker access to your source tree is finicky.

Next: [05 · Language Drivers](05-language-drivers.md).
