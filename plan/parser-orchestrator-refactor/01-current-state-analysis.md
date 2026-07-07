# Current State Analysis (evidence)

All paths relative to `src/backend/` unless noted.

## 1. The resync pipeline today

```
GraphBuilderOrchestrator.resync()                orchestrator.py:94
│
├── driver_manager.warmup_drivers()              orchestrator.py:109
├── FileScanner.scan()                           orchestrator.py:123
│     └── os.walk + sha256 per file              discovery/scanner.py:75
│
├── ChangeDetector.detect_changes(scan)          orchestrator.py:135
│     ├── get_all(FileSchema), get_all(FolderSchema)   change_detector.py:365   ← FULL DOCS
│     ├── read_or_inject_folder_id per folder    change_detector.py:376  ← RPC per path
│     ├── read_or_inject_file_id per file        change_detector.py:381  ← RPC per path
│     ├── _build_parent_maps (DB side)           change_detector.py:103  ← NO GROUP EDGES
│     ├── _build_current_parent_maps (FS side)   change_detector.py:183
│     └── classify: parent mismatch ⇒ MOVE       change_detector.py:256,328
│
├── _process_changes                             orchestrator.py:175
│     ├── collector.sync_structure               collector.py:54
│     │     ├── structure_repo.flush_batch       → COMMIT 1
│     │     └── structure_repo.update_batch      → COMMIT 2 (read-modify-write)
│     │
│     ├── Phase 1 process_collection_phase       phase_processor.py:157
│     │     ├── per file: driver.parse_file(resolve_mro=True)   collector.py:134
│     │     ├── per file: _build_existing_map (WOQL path query) ast_processor.py:65
│     │     └── flush every batch_size=5000:
│     │           code_element_repo.flush_batch  → COMMIT(s) 3..N (chunks of 2000 queries)
│     │
│     └── Phase 2 process_analysis_phase         phase_processor.py:242
│           ├── per file: get_children AGAIN     body_parser.py:173
│           ├── per file: driver.parse_file AGAIN (resolve_mro=False)  body_parser.py:199
│           ├── per scope: driver.resolve_calls
│           └── buffered flushes:
│                 call_repo.create (insert chunks 60k)      → COMMIT(s)
│                 call_repo.flush_delete_move (chunks 5000) → COMMIT(s)
│
└── socket emit project:updated                  orchestrator.py:164
```

Trigger points: `api/v1/project_routes.py:121` (manual resync) and
`core/watcher/service.py:115` (watchdog, 0.5 s debounce → full resync per save burst).

## 2. Group transparency: where it works, where it breaks

A group is a graph-only container. Disk knows nothing about it. Three group families:

- `StructureGroupSchema` — child edge `structure_group` on folders (and groups)
- `CodeElementGroupSchema` — child edge `code_element_group` on files/classes/functions
- `CallGroupSchema` — child edge `call_group`

Edge-field registry: `core/repository/utils/child_raw.py:19-60`.

### ✅ Works: call diffing skips groups

`core/parser/graph_builder/call_graph/diff_calulator.py:127-151` —
`_flatten_calls_skipping_groups()` recurses through nodes with `node_type == "group"` so
call comparison sees the *logical* children. **This is the pattern to generalize.**

Lineage queries are also group-aware:
`code_element_repo.get_node_lineage` (`code_elements/code_element_repo.py:357`) traverses
`<structure_group|<code_element_group` inverse edges, and `structure_repo.get_children`
(`structure/structure_repo.py:148`) includes group edges in path patterns.

### ❌ Broken: structure change detection

`discovery/change_detector.py`:

- `_build_parent_maps` (line 103) iterates only `folder_children` / `file_children` of
  **FolderNode** snapshots. It never fetches `StructureGroupSchema` docs and never follows
  `structure_group` edges.
- Consequence: a file/folder placed in a structure group has **no entry** in
  `db_file_parent_by_id` (parent `None`), while the filesystem parent map
  (`_build_current_parent_maps`, line 183) says its parent is the physical folder ID.
- Classification (`_classify_file_changes` line 328, `_classify_folder_changes` line 256):
  `db_parent != current_parent` ⇒ `MoveEvent` with `new_parent_id = physical folder`.
- `folder_processor.prepare_batch` / `file_processor.prepare_batch` turn the MoveEvent
  into `plan.move`, and `structure_repo.flush_batch` (line 235-251) deletes the old
  parent triple (the group edge) and adds `folder → child`.

**Net effect: every resync silently moves grouped items back out of their groups.**

### ❌ Broken (differently): code-element sync

`collection/ast_processor.py:_build_existing_map` (line 65):

- `structure_repo.get_children(file_id, exclude_types=[... CodeElementGroupSchema ...])`
  — the path traverses group edges but group nodes are **excluded from results**.
- `child_to_parent` is built from `node.children` of returned nodes only. A function
  inside a group is nobody's child in that map → falls back to `parent_id = file_node.id`
  (line 94).
- For a **top-level** grouped function, the fallback coincidentally equals the desired
  parent (the file) ⇒ no move ⇒ grouping preserved.
- For a grouped **method** (group under a class), fallback = file, desired = class ⇒
  spurious move (`_determine_sync_operations` line 236) ⇒ ripped out of the group.

Same conceptual bug, different failure mode — hence the observed inconsistency.

## 3. Commit behavior

`grep -rn commit_msg app/core | wc -l` → **49** commit-creating call sites.

Per resync (medium change set), commits created:

| Source | Commits |
|---|---|
| `structure_repo.flush_batch` (collector.py:84) | 1 |
| `structure_repo.update_batch` (collector.py:91) | 1 |
| `code_element_repo.flush_batch` chunks (`max_queries_per_code_flush=2000`) | ⌈ops/2000⌉ per 5000-file buffer |
| `call_repo.create` insert chunks (body_parser.py:65, 60k chunk) | ≥1 per flush threshold (10k buffered) |
| `call_repo.flush_delete_move_batch_chunked` (5000 chunk) | ≥1 |
| `flush_content_batch` (structure_repo.py:266) — when used | 1 |

Plus every interactive service action (create/update/move/delete of any node, group ops,
document ops) is its own commit via `BaseRepo` helpers (`base_repo.py:32,113,135,163,294`).

Anti-patterns vs TerminusDB best practice:

- **Read-modify-write updates**: `update_node`/`update_nodes`/`update_batch` fetch full
  docs (`get_by_ids(raw=True)`), merge set-fields in Python, then `update_document` the
  whole doc — 2 round-trips and it rewrites unchanged triples (bigger layers).
  (`base_repo.py:113-161`, `structure_repo.py:121-146`, `code_element_repo.py:75-100`)
- **Full-doc snapshots for detection**: `get_all_documents` per type
  (`change_detector.py:365`) when only `{id, path, hash, parent-edge}` is needed.
- **No layer maintenance**: nothing ever calls TerminusDB `optimize`/squash; commit
  layers accumulate forever.
- **Commit messages** are noise ("Batch: N inserts...") — no sync/session correlation ID.

## 4. Memory / performance

- **Per-file RPC on every resync**: `_extract_current_path_to_id`
  (change_detector.py:376-385) does `read_or_inject_file_id` for *every* scanned path,
  50-concurrent. For unchanged files this is pure waste — the DB already maps path→id,
  and the scanner already computed content hashes. Worse: ID injection *writes to source
  files* on the driver side, which can re-trigger the watcher.
- **Double parse**: Phase 1 `driver.parse_file(resolve_mro=True)` (collector.py:134);
  Phase 2 `driver.parse_file(resolve_mro=False)` on the same content
  (body_parser.py:199).
- **O(project) RAM**: `process_collection_phase` returns `results = [(file_node, content)]`
  for **all** files (phase_processor.py:220-240) and holds it until Phase 2 finishes.
- **Per-file WOQL queries**: `_build_existing_map` (Phase 1) and `get_children` (Phase 2)
  issue one path query per file; could be one query per window.
- **Concurrency mismatch**: `_ANALYSIS_PHASE_CONCURRENCY=10` gathers 10 files, but inside
  `_traverse_and_process` a `Semaphore(1)` (body_parser.py:298) serializes scope
  processing anyway.
- `batch_size` default is 5000 in the orchestrator (orchestrator.py:49) but 4000 in
  PhaseProcessor (phase_processor.py:76); content-chunking by bytes is commented out
  (phase_processor.py:135-141) — payload safety currently off.

## 5. Code organization

- `BaseRepo` mixes CRUD, WOQL path queries, move logic, and field-merge helpers
  (~450 lines). Subclasses override with incompatible signatures
  (`structure_repo.get_by_qnames` returns a dict, base returns a list — LSP violation,
  structure_repo.py:193).
- **Module-level dict mutation**: `structure_repo.move_item/move_batch` (lines 108-119)
  do `STRUCTURE_CHILD_TYPE_TO_FIELD.update(CODE_CHILD_TYPE_TO_FIELD)` — permanently
  mutating a shared constant on first call.
- Error handling: `print(exc)` + `return None/False/[]` throughout repos
  (base_repo.py:53-55,68,78,90 …); orchestrator and body_parser use bare `print()`
  for progress; failures in `_flush_code_element_buffer` are swallowed with a log line
  (phase_processor.py:152-155) leaving partial state "until next sync".
- Duplicated logic: folder/file processors, update-merge routines, move-batch WOQL in
  three repos.

## 6. JSON-RPC layer

Backend server (`app/api/json_rpc/`): single method `register_logs_batch`
(entrypoint.py:42) — exceptions swallowed with `print(ex)` and `ok=True` returned anyway
(entrypoint.py:53-59).

Driver client (`core/parser/drivers/json_rpc_client.py`):

- No retry/backoff; a transient HTTP error fails the file (or the whole detection pass).
- `is_alive()` (line 176) only checks the httpx client object — not the remote process.
- No batch methods: one HTTP round-trip per file for `parse_file`,
  `read_or_inject_file_id`, `resolve_calls`.
- No payload cap / compression for large files; timeout is one global 120 s.

Driver server (`src/lsp/py/vnoc_lsp_python/rpc.py`):

- Every method is `run_in_threadpool` with no concurrency bound — 50 concurrent
  backend calls ⇒ 50 threads sharing one jedi/parso project state.
- `read_or_inject_*` mutate user source files as a side effect of a *read-path*
  (change detection). No dry-run/read-only mode.

These are addressed in phases 3 (call batching) and 5 (hardening).
