# 5 — Repository and service layer

## Why add service methods

`ProjectRepo.create` today assumes a single local `AsyncClient` for both meta inserts and per-db operations. Remote flows need:

- A client (or connection) targeting **remote** for bootstrap (create path only).
- The existing **local** client for meta + `clonedb` + orchestration.

Keeping routes thin suggests:

- **`ProjectRepo`**: Extract **pure DB bootstrap** into something like `async def bootstrap_empty_project_db(client: AsyncClient, name: str, description: str) -> str` returning `db_name`, callable with either local or remote client. Then `create` becomes: `db_name = await bootstrap_empty_project_db(local_clone, ...)` + meta insert + `ProjectNode` (today’s behavior).

- **`ProjectRepo`** (or a small `RemoteProjectRepo` if you want separation):  
  - `create_with_remote(...)` orchestrating Steps 1–4 from flow 3, or  
  - Lower-level methods: `bootstrap_on_client`, `insert_project_meta`, and let `ProjectService` sequence them.

## `ProjectService` (MVP)

Add methods such as:

- `async def create_local_only(name, description, path)` — delegate to existing `project_repo.create` (optional rename of current `create`).
- `async def create_with_remote_bootstrap(name, description, path, remote_config, remote_mode)` — implements [03-flow-create-with-remote.md](./03-flow-create-with-remote.md).
- `async def create_from_remote_clone(name, description, path, remote_config)` — `remote_config.remote_url` is the **full** clone URL; implements [04-flow-clone-existing.md](./04-flow-clone-existing.md).

The service receives **both** clients or a factory from dependencies (e.g. `get_terminus_client` + `get_remote_terminus_client(url, auth)` injected only in routes that need it).

## Dependency injection

- `get_project_service` today builds UoW from default client. For create-only flows you may not have a `ProjectNode` yet; current `create` uses `ProjectService` with a UoW that still has `meta_repos` for `project_repo.create`. Verify `get_project_service` / `Repositories` wiring: `create` only needs meta `project_repo`, not scoped project DB — if UoW requires a dummy project today, adjust so `create_with_remote` can obtain `ProjectRepo` without an existing project.

If the existing DI is awkward, MVP-acceptable approach: inject `AsyncClient` + build `Repositories` / `ProjectRepo` directly in the route for create-only — but prefer fixing DI once so all creation goes through `ProjectService`.

## Testing hooks

- Unit-test `bootstrap_empty_project_db` with a mocked `AsyncClient`.
- Integration tests: optional, behind env flag; document need for test remote or container.

## Code reuse checklist

| Piece | Reuse |
|-------|--------|
| `ensure_schema`, `FolderSchema.create_init_folder` | Same as `project_repo.create` |
| `clonedb` | Same as `versioning/remotes.clone_remote` |
| `RemoteAuth` dict | Same shape as `remotes.py` |
| `slugify` + collision | Same as `project_repo.create` for **local/remote create** paths; **clone** path: collision without local `create_database` (see 04) |
