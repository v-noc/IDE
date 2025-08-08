### Domain Modeling & Aggregates

Aggregates
- Project (root): owns folders/files/virtual roots
- Folder/File (structure): contain functions/classes
- Function/Class (code): own type info, calls, attributes
- Package (external): import references, metadata
- VirtualFolder/File (organization): link to code elements

Principles
- Composition over inheritance; mixins for cross-cutting (e.g., Positioned)
- Explicit invariants: no cycles in `contains`; unique names per scope (optional)
- Value objects for properties to avoid leaking persistence concerns

Identifiers & QNames
- `_id` is storage identity; `qname` is logical identity
- Domain methods accept qnames where appropriate; repos resolve

Relationships
- Edge types: belongs_to, contains, virtual_contains, calls, uses_import, implements, links_to
- Domain produces EdgeProposals; persistence materializes them

Validation
- Pydantic for DTOs; domain enforces business rules
- Precondition checks at service layer; postconditions in domain

## Step-by-step: Implement a minimal domain aggregate

1) Define EdgeProposal used by domain
```python
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class EdgeProposal:
    collection: str
    from_id: str
    to_id: str
    props: Optional[Dict[str, Any]] = None
```

2) Implement `Project` with behavior emitting proposals
```python
class Project:
    def __init__(self, model: dict):
        self.model = model  # { _id, _key, name, path }
        self._pending_edges: list[EdgeProposal] = []

    @property
    def id(self) -> str:
        return self.model["_id"]

    def add_virtual_folder(self, folder_id: str) -> None:
        self._pending_edges.append(
            EdgeProposal(collection="contains", from_id=self.id, to_id=folder_id)
        )

    def collect_edges(self) -> list[EdgeProposal]:
        edges, self._pending_edges = self._pending_edges, []
        return edges
```

3) Service consumes proposals and passes to UoW/GraphWriter
```python
project = Project(model=repo.get(project_id))
project.add_virtual_folder(folder_id)
edges = project.collect_edges()
uow.edges.add_many(edges)
```

Notes
- Domain holds no AQL or db code; it only emits intent
- UoW + GraphWriter realize the intent transactionally 