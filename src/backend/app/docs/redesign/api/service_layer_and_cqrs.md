### Service Layer & CQRS

Commands (write)
- Use UoW to load aggregates and perform mutations
- Gather Node/EdgeProposals; commit via GraphWriter
- Idempotency via upserts and unique edge constraints

Queries (read)
- Read repositories; no UoW involvement
- Projected DTOs; avoid over-fetching
- Heavier traversals are paginated and cached

Example flows
- CreateProjectCommand → ProjectService.create(name, path)
- GetProjectListQuery → ProjectReadRepo.list(offset, limit)

Validation & DTOs
- Pydantic schemas at boundaries
- Domain validates invariants internally

## Step-by-step: Implement a command and a query

1) Define DTOs
```python
from pydantic import BaseModel

class CreateProjectCommand(BaseModel):
    name: str
    path: str

class ProjectDto(BaseModel):
    key: str
    name: str
    path: str
```

2) Implement service methods
```python
class ProjectService:
    def __init__(self, uow_factory):
        self._uow_factory = uow_factory

    def create(self, cmd: CreateProjectCommand) -> ProjectDto:
        with self._uow_factory() as uow:
            node = NodeProposal(collection="nodes", document={
                "node_type": "project",
                "name": cmd.name,
                "path": cmd.path,
            })
            uow.nodes.add(node)
        # Reload for response (or return assembled DTO)
        project = uow.projects.get_by_name(cmd.name)
        return ProjectDto(key=project["_key"], name=project["name"], path=project["path"])

    def list(self, offset=0, limit=50) -> list[ProjectDto]:
        # read path does not need UoW
        rows = self._uow_factory().projects.list(offset=offset, limit=limit)
        return [ProjectDto(key=r["_key"], name=r["name"], path=r["path"]) for r in rows]
```

3) Wire into FastAPI route
```python
from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/projects", response_model=ProjectDto)
def create_project(cmd: CreateProjectCommand, service: ProjectService = Depends()):
    return service.create(cmd)

@router.get("/projects", response_model=list[ProjectDto])
def list_projects(service: ProjectService = Depends()):
    return service.list()
```

4) CQRS note
- Writes go through `ProjectService` with UoW
- Reads can use lightweight read repos or direct AQL projections 