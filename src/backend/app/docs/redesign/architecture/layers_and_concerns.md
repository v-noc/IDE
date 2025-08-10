### Layered Design & Cross-Cutting Concerns

Layer contracts
- Transport → Application: DTOs (commands/queries), no domain types
- Application → Domain: value objects + repository interfaces
- Domain → Persistence: EdgeProposals/NodeProposals, no AQL

Cross-cutting
- Validation: Pydantic at edges, invariants in domain
- Observability: per-use-case logging context; trace AQL timings
- Errors: domain errors mapped to HTTP with problem+json
- Configuration: single settings module; inject via providers

Extensibility
- New node/edge types added by extending repositories + GraphWriter mappings
- Feature flags for experimental traversals

Performance guidelines
- Batch by aggregate and edge type
- Prefer bounded traversals and indexes
- Cache hot read models (LRU/Redis) with TTL

## Step-by-step: Enforce layer boundaries

1) Transport receives DTO, calls service
```python
@router.post("/projects")
def create_project(cmd: CreateProjectCommand, svc: ProjectService = Depends()):
    return svc.create(cmd)
```

2) Service uses UoW and domain, returns DTO
```python
with uow_factory() as uow:
    node = NodeProposal(collection="nodes", document={"node_type": "project", "name": cmd.name, "path": cmd.path})
    uow.nodes.add(node)
return ProjectDto(key=..., name=..., path=...)
```

3) Domain emits proposals only
```python
project.add_virtual_folder(folder_id)
edges = project.collect_edges()
``` 