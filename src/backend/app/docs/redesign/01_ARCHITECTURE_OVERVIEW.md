### 01. Architecture Overview

Goals
- Scalable graph-first ORM on ArangoDB
- Clear layering, minimal coupling, high testability
- Composition-first domain model; inheritance only for base concerns
- Bulk-friendly, observable, parallelizable, incremental

Layers
- Transport: FastAPI routes (unchanged conceptually)
- Application: Services (commands/queries) orchestrate use cases
- Domain: Rich objects (Project, Folder, File, Function, Class, Package, Virtual*) with behavior
- Persistence: Repositories + Unit of Work (UoW) over collections
- Storage: ArangoDB (nodes/edges), AQL

Key changes
- Introduce Repository interfaces per aggregate (ProjectRepository, NodeRepository, EdgeRepository)
- Add Unit of Work to group writes transactionally
- Replace ad-hoc collection usage in domain with repositories
- Formalize SymbolIndex (was SymbolTable) for cross-file resolution (read-only in app layer)
- Central GraphWriter for batched node/edge persistence

High-level flow
1) Service receives command
2) Repos load aggregates; Domain mutates
3) UoW tracks changes; on commit -> GraphWriter persists in batch
4) Queries go through read-model repos (CQRS-friendly)

Concurrency and scale
- Per-request UoW; repositories scoped to UoW
- Bulk APIs for create/update edges/nodes
- Indexing and traversal helpers encapsulated in repos 