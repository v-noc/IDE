### Language-Agnostic Parser Architecture

This architecture lets you plug different language frontends (Python/ESTree/TypeScript/Rust) into a shared analysis pipeline and graph backend.

#### High-level pipeline
1) Discovery: enumerate files, filter by config/ignore
2) Frontend parse: use language-native parser to produce a language AST
3) Normalization: map language AST → Unified IR (UST)
4) Stage 1 (Declaration Pass): extract declarations (modules, types, functions)
5) Index barrier: commit declarations to a shared `SymbolIndex`
6) Stage 2 (Detail Passes): imports/deps, types, calls, control flow
7) Graph writer: batch persistence to storage/graph
8) Reporting: issues, metrics, summaries

#### Core components
- UST (Unified Syntax Tree): minimal cross-language node kinds with source spans
  - module, import, class/type, function/method, variable, call, attribute/name, control-flow nodes
- SymbolIndex: language-agnostic multi-index for modules, types, functions, packages
- Pass contracts: typed DTOs (DeclarationResult, DetailResult)
- Visitors: pure analyzers over UST producing IR (edges, facts, issues)
- GraphWriter: single sink for bulk persistence

#### Language adapters
- Python: `ast` → UST via adapter (maps FunctionDef/ClassDef/Import/Match/etc.)
- JS/TS: ESTree/TS AST → UST (Babel/TypeScript compiler API)
- Rust: syn/hir → UST (via `syn` crate or rust-analyzer JSON)

Each adapter must:
- Provide qname rules (module path + nested scopes)
- Normalize imports (default/named/namespace for JS, use/import/mod for Rust)
- Emit language tags on UST nodes for downstream specialization when needed

#### Parallelism & incremental
- Per-file passes are independent; run with a worker pool
- Barrier after Stage 1 ensures consistent global index for Stage 2
- Use content hashes and a reverse import graph to re-analyze only affected files

#### Extensibility hooks
- Feature flags per pass (enable/disable types, CFG)
- Pluggable resolvers: package resolver, type resolver, control-flow backend
- Telemetry adapter for metrics

#### Minimal contracts (language-neutral)
- DeclarationResult: nodes + parent relationships + issues
- DetailResult: edges (UsesImport, Calls, Contains), TypeFacts, CFG fragments + issues
- Issue: code, severity, span, message

See also: architecture/PIPELINE_AND_CONTRACTS.md 