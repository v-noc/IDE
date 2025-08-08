### Architecture Overview

Goals
- Scalable graph-first ORM on ArangoDB
- Clear layering, minimal coupling, high testability
- Composition-first domain model; inheritance only for base concerns
- Bulk-friendly, observable, parallelizable, incremental

Layers
- Transport: FastAPI routes
- Application: Services (commands/queries) orchestrate use cases
- Domain: Rich objects (Project, Folder, File, Function, Class, Package, Virtual*) with behavior
- Persistence: Repositories + Unit of Work (UoW) over collections
- Storage: ArangoDB (nodes/edges), AQL

Key changes
- Repository interfaces per aggregate (ProjectRepository, NodeRepository, EdgeRepository)
- Unit of Work to group writes transactionally
- Replace ad-hoc collection usage in domain with repositories
- SymbolIndex for cross-file resolution (read-only in app layer)
- Central GraphWriter for batched node/edge persistence

Sequence diagram (high level)
1) Service receives command
2) Load aggregates via repositories
3) Domain mutates and emits EdgeProposals
4) UoW tracks changes; on commit → GraphWriter persists in batch
5) Queries go through read-model repos (CQRS-friendly)

Non-functional concerns
- Observability: structured logs, operation IDs, AQL timing
- Idempotency: unique constraints + upsert patterns
- Concurrency: optimistic by default, retry on conflicts
- Performance: bulk writes, pagination, bounded traversals 