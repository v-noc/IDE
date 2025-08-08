### Python Parser: Architecture Audit and Improvement Plan

#### Executive summary
- The current pipeline (ProjectScanner → PythonFileParser → Visitors → DB) is clear and already split into declarative and detail passes with a SymbolTable and AST cache.
- Main opportunities: remove duplicated AST work, harden SymbolTable semantics, decouple analysis from DB side-effects, batch DB writes, introduce incremental & parallel execution, and standardize contracts across passes.
- This doc proposes a phased plan to make it fast, scalable, and readable, while laying groundwork for multi-language reuse.

---

### Current pipeline overview
- Entrypoint: `ProjectScanner.scan()`
  - Pass 0: discover files via `FileNavigator`
  - Pass 1: create folder/file nodes + `BelongsTo`/`Contains` edges
  - Pass 2: declarations (functions/classes) via `PythonFileParser.run_declaration_pass`
  - Pass 2b: builds hierarchy again via `DeclarationVisitor` to decide `ContainsEdge` parenting
  - Pass 2c: persist nodes + edges
  - Pass 3: detail pass via `PythonFileParser.run_detail_pass` → dependency + calls + basic type inference
- Shared state: `SymbolTable` (qname→id, imports, types), `ASTCache`
- Detail visitors: `DependencyVisitor` (import/use), `TypeInferenceVisitor`, `CallVisitor`

---

### Strengths
- Two-pass design enables declaration-first indexing followed by resolution.
- Dependency analysis separates import processing and usage detection with a small, testable API.
- Early type inference hooks are in place to support call resolution and class field typing.
- `FileNavigator` abstracts discovery and filtering; `ASTCache` exists to avoid re-parsing.

---

### Gaps and issues (with concrete fixes)
1) Duplicate parsing and hierarchy work
- Symptom: In `ProjectScanner.scan` the code re-parses AST and re-runs `DeclarationVisitor` after `run_declaration_pass` already parsed the file.
- Fix: Have `run_declaration_pass` return both: (a) DB nodes to create, (b) a compact parent map `{child_qname → parent_qname}` or a stable hierarchical IR. Eliminate the second parse.

2) SymbolTable semantics are underspecified
- `is_local_module` uses naive prefix checks on `_qname_to_id` and can misclassify packages; also `get_all_packages` guesses using heuristics.
- Fixes:
  - Maintain separate indexes: `module_index` (file/module qnames), `type_index` (classes), `function_index`, `package_index`.
  - Provide explicit API: `is_known_module(qname)`, `is_known_symbol(qname, kind)`.
  - Add a trie or prefix map for module paths for O(log n) prefix queries.

3) DB side-effects inside visitors
- `TypeInferenceVisitor` and others call DB to fetch and mutate domain objects in-visit; this couples analysis to persistence and hurts testability/perf.
- Fix: Visitors should emit pure IR (e.g., NodeUpdates, EdgeProposals). A commit phase in `ProjectScanner` (or a `GraphWriter`) batches persistence.

4) Chatty, unbatched DB writes
- Nodes/edges are written one-by-one inside loops.
- Fix: Accumulate per-file batches (nodes, edges, property updates) and bulk write per file or per N items. Provide `collections.*.bulk_create([...])` and `bulk_update([...])`.

5) AST cache inconsistency
- `ASTCache` stores in `_file_asts`; `ProjectScanner.get_scan_summary` reads `ast_cache._cache` which doesn’t exist.
- Fix: Rename to a single private field (e.g., `_cache`) and update all usages. Add `size()` accessor and forbid direct attribute access.

6) `FileNavigator` ignore file format
- It attempts to parse `.gitignore` as TOML with `ignore.patterns`. That’s incorrect and causes silent mis-filtering.
- Fix: Support both (a) a project config TOML (e.g., `v-noc.toml`) with `ignore.patterns`, and (b) standard `.gitignore` using line-based patterns via `pathspec.PathSpec.from_lines`. Detect by filename.

7) Call resolution heuristics
- `CallVisitor` contains debug prints and broad heuristics (e.g., treat any qname ending in name as class). This may create wrong edges.
- Fixes:
  - Leverage `TypeInferenceVisitor` outputs formally via `VisitorContext` (e.g., `variable_types`, `function_return_types`).
  - Add parent links or a light CFG to resolve `self` and instance types more reliably.
  - Remove prints, add structured logging behind a debug flag.

8) Error handling and diagnostics
- Many `print` warnings; no structured error objects.
- Fix: Introduce `AnalysisIssue` with severity, file, span, and code. Collect per-file and expose in scan summary and logs.

9) Contracts between passes
- There’s no typed contract that guarantees what `run_declaration_pass` and `run_detail_pass` must return.
- Fix: Introduce typed DTOs:
  - `DeclarationResult { nodes: [...], parent_of: Map<childQname,parentQname> }`
  - `DetailResult { edges: [...], typeFacts: [...], issues: [...] }`
  - `ScanSummary { files, symbols, packages, issues }`

10) Parallelism and incremental
- All files are processed sequentially; on large codebases this will be slow.
- Fix:
  - Make per-file analysis stateless and parallelizable, gate shared tables by staged commits (per-file symbol pre-index → barrier → detail passes).
  - Add a content-hash index to skip unchanged files, invalidating dependents via import graph.

---

### Proposed target architecture (Python)

```
ProjectScanner
  ├─ Discovery: FileNavigator → files
  ├─ Stage 1 (parallel): DeclarationPass(file) → DeclarationResult
  │     └─ Stage 1.5: SymbolIndex.commit(modules, types, functions)
  ├─ Stage 2 (parallel): DetailPass(file, SymbolIndex) → DetailResult
  ├─ Stage 3: GraphWriter.bulkCommit(nodes, edges, updates)
  └─ Reporting: Issues, Metrics, Summary

Shared
  ├─ SymbolIndex (thread-safe, versioned)
  ├─ ASTCache (LRU, hash-keyed)
  ├─ Config + Ignore
  └─ Logger + Telemetry
```

Key properties:
- Pure analysis passes with typed results
- Central `GraphWriter` batches persistence
- Symbol index separated per kind; versioned for incremental rebuilds
- Parallel-safe barriers between stages

---

### Concrete, actionable improvements (by theme)

Performance
- Add content-hash cache: `hash = blake3(file_bytes)`, memoize AST and `DeclarationResult` by hash.
- Parallelize per-file passes using a worker pool. Use a barrier after Stage 1 to freeze the module index before Stage 2.
- Batch DB writes per file and per phase. Provide bulk endpoints in `collections`.
- Avoid re-parsing: use `ASTCache` exclusively; forbid ad-hoc `ast.parse` outside `PythonFileParser`.

Modularity & readability
- Introduce DTOs for pass outputs and a `GraphWriter` abstraction.
- Push DB interactions to a single sink layer.
- Replace heuristic helpers with `SymbolIndex` queries with explicit kinds.
- Remove prints; use structured logging with per-file correlation IDs.

Correctness
- Strongly type `SymbolTable`/`SymbolIndex` with separate maps for modules, classes, functions, packages.
- Implement parent-tracking during AST walk to enable reliable `self`/instance method resolution.
- Normalize qname construction in one utility and reuse across modules.

Resilience
- Introduce `AnalysisIssue` and collect throughout passes.
- Fail-soft per file; continue the scan and summarize issues.

Developer experience
- Add golden tests for:
  - Import resolution (absolute, relative, alias, `from x import y`)
  - Call resolution (local, module.func, self.method, constructor)
  - Type extraction (annotations, simple inference)
  - Hierarchy/contains edges
- Provide debug CLI: `v-noc parse --file <path> --json` printing `DeclarationResult`/`DetailResult`.

---

### Specific refactors (suggested diffs)
- `ASTCache`
  - Rename `_file_asts` → `_cache`; add `size()`, `keys()`, hide private fields.
- `FileNavigator`
  - Support both `.gitignore` (line-based) and `v-noc.toml` (`ignore.patterns`). Auto-detect.
- `PythonFileParser.run_declaration_pass`
  - Return `DeclarationResult` with `nodes` and `parent_of` map; remove any external re-visiting.
- `ProjectScanner.scan`
  - Remove the second `ast.parse`/`DeclarationVisitor` pass.
  - Accumulate `nodes` and `contains` edges using `parent_of`.
  - Batch writes; collect `issues` from both passes.
- `SymbolTable` → `SymbolIndex`
  - Maps: `moduleByQname`, `classByQname`, `functionByQname`, `packageByQname`.
  - API: `addModule`, `addFunction`, `addClass`, `addPackage`, `resolve(kind, qname)`, `isKnown(kind, qname)`.
- Visitors
  - Remove DB calls; emit `EdgeProposals` and `TypeFacts` to `VisitorContext.results`.
  - Add parent pointers or prepass to annotate `ast` nodes with parents.

---

### Incremental and parallel execution plan
1) Stage 0: Symbol warmup
- For all files (parallel), compute hash. If unchanged, skip fully.
- For changed files, parse, compute declarations → `DeclarationResult`.
- Commit modules/types/functions to `SymbolIndex`.
2) Stage 1: Detail
- For changed files (parallel), run detail visitors with read-only `SymbolIndex` → `DetailResult`.
3) Stage 2: Persist
- Bulk commit nodes/edges/updates; record `fileHash` and `symbolIndexVersion`.

Dependency-aware invalidation
- Maintain reverse import graph: when file A changes, invalidate dependent files.

---

### Observability & limits
- Add metrics: files scanned, AST cache hit rate, time per phase, DB ops, queue depth.
- Add guards: maximum edges per file, visitor recursion depth, timeout per file.

---

### Roadmap (phased)
- Phase 1 (1–2 days): Fix `ASTCache` field, `FileNavigator` ignore parsing, remove prints, add structured logs.
- Phase 2 (3–5 days): DTO contracts, decouple DB from visitors, central `GraphWriter`, batch writes.
- Phase 3 (1 week): Parallel worker pool, barrier between passes, content-hash cache.
- Phase 4 (1–2 weeks): Strengthen `SymbolIndex`, parent links, better call/type resolution, issue collection.
- Phase 5 (ongoing): Incremental rebuilds + dependency invalidation; telemetry and limits.

---

### Appendix: Minimal DTOs
```ts
// Declaration
type Qname = string;
export interface DeclarationResult {
  nodes: Array<FunctionNode | ClassNode>;
  parentOf: Record<Qname, Qname | undefined>; // child → parent
  issues: AnalysisIssue[];
}

// Detail
export interface DetailResult {
  edges: Array<UsesImportEdge | CallEdge>;
  typeFacts: Array<TypeFact>;
  issues: AnalysisIssue[];
}

export interface AnalysisIssue {
  code: string; // e.g., PY1001
  message: string;
  severity: 'info' | 'warning' | 'error';
  file: string;
  span?: { line: number; col: number; endLine: number; endCol: number };
}
``` 