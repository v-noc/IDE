### 07. Patterns and Extensibility

Patterns
- Repository + Unit of Work: persistence orchestration
- Adapter: Pydantic ↔ domain entities ↔ storage
- Strategy: pluggable ID generation, qname rules, package resolution
- Decorator: add caching/logging to repos without changing interface
- Visitor: AST processing pipeline (already in parser) formalized via contracts
- Composite: virtual folders/files as tree with uniform ops

Extension points
- GraphWriter backends (sync, async, bulk sizes)
- Package resolver (local vs external)
- Query layer (AQL templates or typed DSL)
- Caching policy (per-request, LRU)

Feature flags
- Toggle heavy passes (type inference, CFG) and bulk write thresholds 