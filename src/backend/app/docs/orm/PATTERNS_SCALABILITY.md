### Scalability & Modularization Patterns

Module boundaries
- Group models/edges by bounded context (projects, code, virtual)
- Keep registry centralized; expose only typed collections to callers

Composition-first
- Domain services compose collections and models (e.g., `CodeGraphManager`)
- Keep ORM small; business logic lives in domain layer

Bulk operations
- Add `bulk_create`/`bulk_update` for nodes/edges; commit per file/feature
- Use AQL `UPSERT` for idempotent writes

Incremental processing
- Track content hashes to skip reprocessing; store in node properties

Parallelism
- Per-file/domain operations can run in worker pools; avoid global mutable state

Caching
- Layered cache: per-request memoization, process-level LRU for hot reads

Multi-tenancy
- Separate DB per tenant/project or prefix keys; keep isolation strategy simple

Observability
- Metrics per collection: ops/sec, latency, errors; slow query logs 