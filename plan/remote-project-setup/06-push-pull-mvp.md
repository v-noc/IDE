# 6 — Push / pull (MVP)

## Current state

`src/backend/app/api/v1/versioning/remotes.py` exposes:

- `POST .../clone` — admin-level `clonedb` (already useful for ad-hoc clones).
- `POST .../push`, `pull`, `fetch` — scoped to `get_project_uow` (project DB + branch).

Push already accepts optional `remote_auth` per request.

## MVP stance

- **No server-side vault** for credentials.
- **No required storage** of `remote_url` on `ProjectSchema` for push/pull to work — users can keep using push/pull with whatever remote is configured on the Terminus side (`origin`), or we document that they must add remotes via Terminus CLI/API if not using URL in our API.

If Terminus requires a remote to be registered by name (`origin`), clarify in product docs:

- Either users configure remotes outside V-NOC, or
- A small follow-up endpoint `POST /projects/{id}/remotes` adds `origin` with URL (still passing auth per call or once) — **post-MVP** unless trivial.

## Alignment with creation flows

- **create_remote**: After initial clone, local DB should track the remote for default push. Terminus may auto-set `origin` from `clonedb` — verify in your Terminus version. If not, document manual `remote add` or add one helper endpoint later.
- **clone**: Same as above.

## API consistency

- Reuse **`RemoteAuth`** model across `CreateProjectRequest.remote` and push/pull bodies.
- Consider moving shared models to `app.api.schemas.remotes` (or similar) to avoid drift between `project_routes.py` and `versioning/remotes.py`.

## Security note

Auth travels in request bodies over HTTPS; avoid logging `key`. Same as current clone/push handlers.
