# Phase 3 / Step 2 — ID resolution without per-file RPC

Problem being removed: `change_detector._extract_current_path_to_id`
(change_detector.py:376-385) calls `read_or_inject_file_id` / `read_or_inject_folder_id`
over JSON-RPC for **every scanned path on every resync**, 50-concurrent. Cost: N HTTP
round-trips + driver-side file reads; worse, the *inject* half **writes into user
source files** during what should be a read-only detection pass (and can re-trigger the
watcher — see Phase 6).

## Resolution ladder (top — cheapest first)

For each scanned path, resolve its stable ID:

```
1. path ∈ snapshot.ids_by_path AND scan.hash == snapshot.hash
       → id from snapshot                                  (unchanged file: FREE)
2. path ∈ snapshot.ids_by_path AND hash differs
       → id from snapshot                                  (modified in place: FREE)
   ⚠ guard: file could have been replaced by a different file (delete+create).
     The ID lives IN the file (docstring/jsdoc) — a replaced file carries either no id
     or its old id. Verify lazily: these files get parsed in the window anyway, and
     parse returns the true file_id; if it contradicts the snapshot id → reclassify
     (delete+new) before staging. No extra I/O — parse already happens.
3. path ∉ snapshot, scan.hash ∈ snapshot.ids_by_hash
       → moved-file candidate: id = matching row           (moved: FREE, confirmed
         by same lazy parse-check as (2))
4. otherwise (truly new or un-id'd)
       → batch: driver.read_or_inject_file_ids([paths])    (ONE RPC per language
         per sync — batch method added in Phase 5; until then, keep per-file calls
         but ONLY for this small set)
```

Folders: same ladder minus hash — path match wins; unknown folders go to the batch
inject call. A moved folder is detected by its (already resolved) children's ids, or by
the folder id read during (4).

## Small persistent cache (middle)

`graph_builder/discovery/id_cache.py` — per-project in-process map:

```python
{abs_path: (mtime_ns, size, file_id)}
```

- Populated after every sync; consulted before the ladder to skip even the hash lookup
  for step-1 hits (mtime+size unchanged ⇒ trust cached id).
- Invalidation: mtime/size mismatch falls through the ladder; deleted paths pruned by
  scan diff.
- Process-local only (the backend is a long-lived FastAPI process; watcher syncs reuse
  it). No disk persistence — cold start pays one snapshot query, which is already cheap.

## What changes where (bottom)

1. `change_detector.detect_changes` gains
   `id_resolution = IdResolver(snapshot, id_cache, driver_manager)`; the two
   `_extract_current_path_to_id` gather-blocks collapse into
   `await id_resolution.resolve(scan_result)` returning the same
   `current_*_id_by_path` maps.
2. The lazy verification hook: `collector.process_file` already receives
   `parse_result` containing the injected/declared file id — add a check
   `parse_result.file_id == expected_id`, on mismatch emit a
   `ReclassifiedChange` back to the session (new file + delete of the stale row) before
   ops are staged. Wire as a callback on the window runner (step 03).
3. Delete `_gather_ids` / `_extract_current_path_to_id` / `_invert_path_id_map`-based
   flow once the resolver lands (invert map survives inside the resolver).
4. Metrics: log per sync `{free_hits, hash_moves, rpc_lookups}` — the acceptance number
   for this step is `rpc_lookups == new files only`.

## Edge cases

- **Copied file** (same hash, original still present): step 3 requires path absent from
  snapshot AND the matched row's path absent from scan — otherwise treat as new.
- **Files where injection is impossible** (read-only FS, syntax error blocking CST):
  driver returns `modified=false` + no id today; resolver marks the path `unidentified`,
  detector falls back to path-keyed identity for that file (documented limitation, same
  as current behavior on failure, change_detector.py:144-151).
- **Hash collisions across languages** (empty `__init__.py` files all share a hash):
  candidate matching prefers same basename + same parent dir before accepting a move;
  otherwise treat as new. Empty-file ids resolve via (1)/(2) path match anyway.
