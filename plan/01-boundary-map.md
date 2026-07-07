# Boundary Map: What Moves vs What Stays

This document maps every module in `src/backend/app/core/parser/` to its destination.

## Legend

| Symbol | Meaning |
|--------|---------|
| **→ DRIVER** | Moves to the Python language driver (separate process) |
| **STAYS** | Remains in the backend |
| **SHARED** | Used by both sides (protocol models) |
| **MODIFIED** | Stays in backend but gets rewired to call driver |
| **DELETE** | Remove (dead code) |

---

## `parser/ast/`

| File | Current Role | Destination | Notes |
|------|-------------|-------------|-------|
| `models.py` | AST node models (`BaseNode`, `FunctionNode`, `ClassNode`, `CallNode`, `NodePosition`) | **SHARED** | Becomes the protocol contract. Both the driver response and backend parsing use these types. Keep in backend, driver has its own copy or imports via shared package. |
| `parser.py` | `JediParser` — parso-based AST building | **→ DRIVER** | Core of the Python parser. Uses `parso.parse()` to walk `Class`/`Function`/`atom_expr` nodes. |
| `id_injector.py` | `IDInjector` — libcst `CSTTransformer` for injecting `ID:` into docstrings, `inject_module_metadata` for FileID/FolderID | **→ DRIVER** | Python-specific. JS/TS will use comments or sidecar files. |
| `scanner.py` | `scan()` — orchestrates `inject_ids` → `JediParser.parse()` | **→ DRIVER** | Thin glue between injector and parser. Becomes a driver-internal function. |
| `visitor.py` | Incomplete `CodeStructureVisitor` stub | **DELETE** | Not wired into any pipeline. Undefined symbols. Dead code. |

---

## `parser/jedi_adapter/`

| File | Current Role | Destination | Notes |
|------|-------------|-------------|-------|
| `manager.py` | `JediProjectManager` — Jedi project/script/environment setup | **→ DRIVER** | Configures `jedi.Script`, `jedi.Project`, `InterpreterEnvironment`. Stays internal to the Python driver. |
| `resolver.py` | `MROResolver` — resolves class MRO via Jedi private API (`py__mro__`) | **→ DRIVER** | Exposed as a `resolve_mro` JSON-RPC method. |
| `call_resolver/call_resolver.py` | `CallHierarchyResolver` + `CallFrameStack` — Jedi-based call target resolution | **→ DRIVER** | Exposed as a `resolve_calls` JSON-RPC method. `CallFrameStack` becomes a shared protocol model. |

---

## `parser/graph_builder/`

### Top level

| File | Current Role | Destination | Notes |
|------|-------------|-------------|-------|
| `orchestrator.py` | `GraphBuilderOrchestrator` — wires scan → change detect → collect → analyze | **MODIFIED** | Remove direct `JediProjectManager` import. Initialize driver client instead. Pass client to sub-components. |
| `progress.py` | `ProgressTracker` — socket-based progress events | **STAYS** | No language-specific code. |
| `performance.py` | `PerformanceTracker` — timing metrics | **STAYS** | No language-specific code. |

### `graph_builder/discovery/`

| File | Current Role | Destination | Notes |
|------|-------------|-------------|-------|
| `scanner.py` | `FileScanner` — walks project for `.py` files, respects `.gitignore` | **MODIFIED** | Currently hardcoded to `.py`. Needs to accept file extensions from driver config. Core logic (walk, ignore, hash) stays. |
| `change_detector.py` | `ChangeDetector` — compares DB vs disk, produces `ChangeSet` | **STAYS** | Works on abstract IDs, paths, hashes. No language-specific code. |
| `file_tracker.py` | `FileTracker` — reads/injects `FileID` in module docstring via libcst | **MODIFIED** | Currently calls `inject_module_metadata` (libcst) directly. Will call driver's `read_or_inject_file_id` method instead. |
| `folder_tracker.py` | `FolderTracker` — ensures `__init__.py`, injects `FolderID` | **MODIFIED** | Same as file_tracker. Delegates to driver's `read_or_inject_folder_id`. |

### `graph_builder/collection/`

| File | Current Role | Destination | Notes |
|------|-------------|-------------|-------|
| `collector.py` | `Collector` — orchestrates file processing: read → scan → sync | **MODIFIED** | Currently calls `scan()` directly and creates `MROResolver`. Will call driver's `parse_file` instead. |
| `ast_processor.py` | `ASTProcessor` — maps AST nodes to DB models, syncs with DB | **MODIFIED** | Currently creates `MROResolver` and calls `_resolve_mro` directly. MRO data will come from `parse_file` response (driver resolves MRO during parse). |
| `file_processor.py` | Builds `StructureBatchPlan` for files from `ChangeSet` | **STAYS** | No language-specific code. |
| `folder_processor.py` | Builds `StructureBatchPlan` for folders from `ChangeSet` | **STAYS** | No language-specific code. |
| `structure_batch.py` | `StructureBatchPlan` dataclass | **STAYS** | Pure data structure. |

### `graph_builder/call_graph/`

| File | Current Role | Destination | Notes |
|------|-------------|-------------|-------|
| `builder.py` | `CallChainBuilder` — merges `CallFrameStack`s, diffs, produces `ScopeSyncResult` | **MODIFIED** | Currently creates `CallHierarchyResolver` and calls it directly. Will call driver's `resolve_calls` instead. Merge + diff logic stays. |
| `models.py` | `ResolvedCall`, `ScopeSyncResult` | **STAYS** | Abstract data models for diff output. |
| `diff_calulator.py` | `DiffCalculator` — compares new vs old call trees | **STAYS** | Works on abstract tree types. No language-specific code. |

### `graph_builder/analysis/`

| File | Current Role | Destination | Notes |
|------|-------------|-------------|-------|
| `body_parser.py` | `BodyParser` — Phase 2 analysis: traverse AST, delegate call resolution | **MODIFIED** | Currently calls `scan()` and `CallChainBuilder`. `scan()` call becomes driver's `parse_file`. `CallChainBuilder` already gets modified above. |

### `graph_builder/utils/`

| File | Current Role | Destination | Notes |
|------|-------------|-------------|-------|
| `phase_processor.py` | `PhaseProcessor` — runs collection + analysis phases | **MODIFIED** | Minor: stop passing `JediProjectManager`, pass driver client instead. |
| `visualization.py` | `GraphVisualizer` — optional pyvis/SQL visualization | **STAYS** | Legacy/debug tool. Not in the critical path. |

---

## Summary: New Files to Create

### In the Backend

| File | Purpose |
|------|---------|
| `parser/driver_client.py` | JSON-RPC HTTP client — sends requests to language drivers |
| `parser/driver_manager.py` | Manages driver process lifecycle (start, stop, health check) |
| `parser/driver_config.py` | Driver registry — maps language/extensions to driver URL/port |

### In the Python Driver (`src/drivers/python/`)

| File | Purpose |
|------|---------|
| `server.py` | HTTP server with JSON-RPC 2.0 endpoint |
| `handlers.py` | Method handlers (parse, mro, calls, metadata) |
| `parser.py` | Moved from `parser/ast/parser.py` |
| `id_injector.py` | Moved from `parser/ast/id_injector.py` |
| `scanner.py` | Moved from `parser/ast/scanner.py` |
| `jedi_manager.py` | Moved from `jedi_adapter/manager.py` |
| `mro_resolver.py` | Moved from `jedi_adapter/resolver.py` |
| `call_resolver.py` | Moved from `jedi_adapter/call_resolver/call_resolver.py` |
| `requirements.txt` | `jedi`, `parso`, `libcst`, `pydantic`, driver HTTP deps |

---

## Dependency Flow (Before → After)

### Before
```
orchestrator.py
  → JediProjectManager (jedi)
  → Collector
      → scan() (parso, libcst)
      → MROResolver (jedi)
      → ASTProcessor
  → PhaseProcessor
      → BodyParser
          → scan() (parso, libcst)
          → CallChainBuilder
              → CallHierarchyResolver (jedi, parso)
```

### After
```
orchestrator.py
  → DriverClient (HTTP)
  → Collector
      → DriverClient.parse_file()
      → ASTProcessor (MRO comes from parse_file response)
  → PhaseProcessor
      → BodyParser
          → DriverClient.parse_file()
          → CallChainBuilder
              → DriverClient.resolve_calls()
```

All `jedi`, `parso`, `libcst` imports vanish from the backend.
