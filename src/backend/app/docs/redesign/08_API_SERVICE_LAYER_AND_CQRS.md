### 08. API Service Layer and CQRS

Commands (write)
- Use UoW; gather intents; commit via GraphWriter
- Idempotent operations via upserts and unique constraints

Queries (read)
- Dedicated read repos; no UoW
- Projected DTOs; avoid over-fetching
- Heavy traversals paginated and cached

Benefits
- Clear write/read separation; easy to scale reads independently

Examples
- CreateProjectCommand → ProjectService.create(name, path)
- GetProjectListQuery → ProjectReadRepo.list(offset, limit) 