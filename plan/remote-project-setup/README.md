# Remote project setup — plan index

This folder describes an MVP design for optional **remote-backed** project creation and ongoing **push / pull / clone** behavior. The goal is a small, clear split between two creation paths, reuse of existing versioning endpoints where possible, and room to grow (stored remotes, default auth, CI) without baking that in now.

Read in order:

| Step | File | What it covers |
|------|------|----------------|
| 1 | [01-overview.md](./01-overview.md) | Goals, terminology, what stays local vs remote |
| 2 | [02-request-model.md](./02-request-model.md) | API shape: `RemoteConfig`, mode flag, optional fields |
| 3 | [03-flow-create-with-remote.md](./03-flow-create-with-remote.md) | New project: bootstrap on remote → meta project doc → clone DB locally → orchestrate |
| 4 | [04-flow-clone-existing.md](./04-flow-clone-existing.md) | Existing remote DB: `clonedb` first → meta project doc → orchestrate |
| 5 | [05-repository-and-service.md](./05-repository-and-service.md) | Where logic lives: `ProjectRepo`, `ProjectService`, thin route |
| 6 | [06-push-pull-mvp.md](./06-push-pull-mvp.md) | Ongoing sync: per-request auth, relation to `versioning/remotes.py` |
| 7 | [07-future-extensions.md](./07-future-extensions.md) | Optional next steps after MVP |
| 8 | [08-implementation-checklist.md](./08-implementation-checklist.md) | Ordered checklist for implementation |

**Related code today**

- Project creation and graph bootstrap: `src/backend/app/core/repository/project_repo.py` (`create`), `src/backend/app/api/v1/project_routes.py` (`create_project`).
- Clone / push / pull API: `src/backend/app/api/v1/versioning/remotes.py`.
- Terminus `clonedb`: `src/backend/app/db/terminus_client/database.py`.
