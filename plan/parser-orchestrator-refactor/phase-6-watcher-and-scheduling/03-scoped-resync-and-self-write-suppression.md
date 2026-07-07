# Phase 6 / Step 3 — Scoped resync & self-write suppression

## Scoped resync (top)

New parameter through the pipeline:

```python
@dataclass(frozen=True)
class SyncScope:
    kind: Literal["full", "paths"]
    paths: frozenset[str] = frozenset()     # files AND folders, absolute

async def ProjectService.resync(project_id, scope: SyncScope) -> SyncReport
```

### What scoping changes — and what it must NOT skip

```
SCAN      paths-scope: hash only scope paths + their parent chain
          (scanner gains scan_paths(paths); os.walk skipped)
DETECT    lean snapshot: still FULL (it is one cheap triple query — scoping the DB
          side would miss deletes elsewhere); classification restricted to:
          scope paths ∪ db rows whose path ∈ scope ∪ moved-pair partners
WINDOWS   only files from the scoped ChangeSet (already true — windows follow changes)
FLUSH     unchanged
```

Safety valves — fall back to `FULL` when:

- scope contains a **folder** create/delete/move (children unknown → cheap full),
- DirtyState `overflowed`,
- scope paths > threshold (e.g. 200 — full scan is cheaper than many stat chains),
- first sync after process start (cache cold),
- explicit user request (resync button stays full).

Correctness argument: a paths-scope sync can only *miss* changes outside scope; the
watcher guarantees every change emits an event that lands in some DirtyState, and any
uncertainty (overflow, folder ops) forces FULL. Missed-event insurance: a periodic
low-priority full sync (e.g. on project open + every 30 min idle) — configurable,
default on.

## Self-write suppression (middle)

Two writers touch project files from inside the system:

1. **ID injection** (drivers, for new files — Phase 5 made detection read-only).
2. **Code edits via API** (`code_routes` / playground save flows writing source).

Mechanism — a small registry on the scheduler:

```python
class SelfWriteRegistry:
    def register(self, path: str, content_hash: str, ttl: float = 5.0): ...
    def matches(self, path: str) -> bool:      # consume-on-match
```

- Injection: driver RPC responses already return `modified: bool`
  (protocol.py FileIdResult); when true, the backend knows the path + can hash the
  new content (it has it — parse returns processed content). Register before the
  event can arrive.
- API writes: the service that writes registers in the same call.
- Filter chain step 5 (doc 01) consults `matches(path)`; TTL covers editor/OS event
  latency; consume-on-match so a *real* user edit 2 s later still syncs (hash differs
  anyway → second guard: on match, compare current file hash to registered hash;
  differ → do not suppress).
- This replaces pause/resume entirely — including the API-route injection loop that
  pause never covered (analysis §today-problem 4).

## Interplay with id-cache (Phase 3)

After a scoped sync, update the id-cache/mtime entries only for scope paths — the
cache is what makes the fallback FULL syncs cheap (unchanged files short-circuit),
so the two features compound: watcher keeps scopes small, cache keeps FULLs fast.

## Steps (bottom)

1. `SyncScope` + `scan_paths` on FileScanner + scoped classification in the detector
   (restrict the id-resolution and classify loops to the scope union; snapshot stays
   full).
2. Fallback valves + periodic insurance sync in the scheduler.
3. `SelfWriteRegistry` + registration at both writer sites + filter hook.
4. Metrics: log per sync `{scope_kind, scope_size, changeset_size, duration}` —
   proves the win and catches scopes that always fall back.
