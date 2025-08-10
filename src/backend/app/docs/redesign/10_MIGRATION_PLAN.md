### 10. Migration Plan

Phase 1: Abstractions (low risk)
- Introduce Repository interfaces and UnitOfWork (no behavior change)
- Wrap existing `db/collections` in thin repos

Phase 2: Batch and GraphWriter
- Add GraphWriter and switch bulk writes in parser/manager to use it
- Implement `bulk_create` in Node/Edge ORMs

Phase 3: Domain wrappers
- Move behavior from API/services into domain objects (Project/Folder/etc.)
- Keep Pydantic models as DTOs only

Phase 4: CQRS services
- Split services into read/write; adjust API routes

Phase 5: Indexing and validation
- Create indexes; add background referential integrity job

Phase 6: Cleanup
- Remove direct `collections.*` usage from core; rely on repos

Rollback
- Each phase is reversible; keep feature flags for new code paths 