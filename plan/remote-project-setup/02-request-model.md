# 2 — Request model and API surface

## Extend `CreateProjectRequest`

Today `CreateProjectRequest` has `name`, `description`, `path`. Add:

1. **`remote: RemoteConfig | null`** — Optional. If absent, behavior stays exactly as today (all operations on local Terminus only).

2. **`remote_mode: Literal["none", "create_remote", "clone"]`** — Default `"none"` when `remote` is null; when `remote` is set, require a non-`none` mode.

`RemoteConfig` keeps `remote_url` and `auth`. **The meaning of `remote_url` depends on `remote_mode`** (see below). Align `auth` with `versioning/remotes.py`:

- Use a shared Pydantic model (or import from one module) so `remote_auth` dict shape matches `clonedb` / `push` (`type`, `username`, `key` as needed by `terminus_client`).

## `remote_url` by mode (required contract)

| Mode | `remote_url` |
|------|----------------|
| **`create_remote`** | **Normal** remote server URL — connection target for creating a new DB on that instance (no DB id baked into the string the way clone needs). |
| **`clone`** | **Full** URL: domain **and** remote database identity in the form Terminus expects for `clone_source` (single string; user does not pass a separate DB id field). |

Document both shapes clearly in OpenAPI descriptions (examples help).

### Fields for **clone** mode only

No extra fields beyond `RemoteConfig`: the remote DB is identified **only** by the full `remote_url`. Local `clonedb` **`newid`** comes from project **`name`** (`slugify` + collision rules that **do not** use local `create_database` — see clone flow doc), not from parsing the remote URL.

### Fields for **create_remote** mode

No extra fields beyond `RemoteConfig`: `db_name` on the remote is still chosen as `slugify(name)` (+ collision on the **remote**), same as today’s logic moved to the remote client.

## Validation rules (MVP)

- If `path` does not exist → 400 (unchanged).
- If `remote` is set:
  - `remote_mode == "create_remote"` → require auth; validate URL looks like a **base** server URL (lightweight check or docs-only).
  - `remote_mode == "clone"` → require auth; validate URL is non-empty **full** clone URL (docs + examples; optional pattern check if stable).
- If `remote` is null → ignore `remote_mode` or require `remote_mode == "none"`.

## Response

Keep returning `ProjectTreeNode` from `POST /` after orchestration, as today.

## Error handling

- Distinguish **remote connection / auth failures** (502 or 401-style) from **local failures** (500 with log).
- **Database already exists** on remote during create: mirror local behavior (suffix timestamp) or return 409 — pick one and document; consistency with current local `create` suggests suffix is friendlier.
