### Repositories & Unit of Work

Repositories
- `ProjectRepository`: load/save projects, list virtual folders
- `NodeRepository`: CRUD on nodes by type and qname
- `EdgeRepository`: CRUD on edges by type; bulk operations

Unit of Work
- Tracks new/dirty/deleted nodes and edges
- `commit()` persists via GraphWriter in a transaction
- `rollback()` clears local state

Contracts (TypeScript-like)
```ts
interface UnitOfWork {
  projects: ProjectRepository;
  nodes: NodeRepository;
  edges: EdgeRepository;
  commit(): Promise<void>;
  rollback(): Promise<void>;
}
```

Patterns
- Per-request UoW lifetime (context manager)
- Repositories receive UoW-scoped db handle

## Step-by-step: Implement Repositories and UoW

1) Define proposal types to decouple domain from persistence
```python
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class NodeProposal:
    collection: str  # e.g., "nodes"
    document: Dict[str, Any]  # { node_type, name, qname, properties }

@dataclass
class EdgeProposal:
    collection: str  # e.g., "contains"
    from_id: str
    to_id: str
    props: Dict[str, Any] | None = None
```

2) Define repository interfaces and a UoW contract
```python
from typing import Protocol, Iterable, Optional

class ProjectRepository(Protocol):
    def get(self, key: str) -> dict | None: ...
    def list(self, offset: int = 0, limit: int = 50) -> list[dict]: ...

class NodeRepository(Protocol):
    def get_by_id(self, node_id: str) -> dict | None: ...
    def get_by_qname(self, qname: str) -> dict | None: ...
    def add(self, node: NodeProposal) -> None: ...

class EdgeRepository(Protocol):
    def add_many(self, edges: Iterable[EdgeProposal]) -> None: ...

class UnitOfWork(Protocol):
    projects: ProjectRepository
    nodes: NodeRepository
    edges: EdgeRepository
    def __enter__(self) -> "UnitOfWork": ...
    def __exit__(self, exc_type, exc, tb) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
```

3) Provide a concrete UoW that buffers changes and uses GraphWriter on commit
```python
class ArangoUnitOfWork:
    def __init__(self, db, graph_writer):
        self._db = db
        self._graph_writer = graph_writer
        self._pending_nodes: list[NodeProposal] = []
        self._pending_edges: list[EdgeProposal] = []
        self.projects = ArangoProjectRepository(db)
        self.nodes = ArangoNodeRepository(db, buffer=self._pending_nodes)
        self.edges = ArangoEdgeRepository(db, buffer=self._pending_edges)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc:
            self.rollback()
        else:
            self.commit()

    def commit(self) -> None:
        self._graph_writer.write(nodes=self._pending_nodes, edges=self._pending_edges)
        self._pending_nodes.clear()
        self._pending_edges.clear()

    def rollback(self) -> None:
        self._pending_nodes.clear()
        self._pending_edges.clear()
```

4) Minimal repository implementations that buffer writes
```python
class ArangoNodeRepository:
    def __init__(self, db, buffer: list[NodeProposal]):
        self._db = db
        self._buffer = buffer

    def get_by_id(self, node_id: str) -> dict | None:
        return self._db.nodes.get(node_id)

    def get_by_qname(self, qname: str) -> dict | None:
        return self._db.nodes.find_one({"qname": qname})

    def add(self, node: NodeProposal) -> None:
        self._buffer.append(node)

class ArangoEdgeRepository:
    def __init__(self, db, buffer: list[EdgeProposal]):
        self._db = db
        self._buffer = buffer

    def add_many(self, edges: Iterable[EdgeProposal]) -> None:
        self._buffer.extend(edges)
```

5) Usage example: create project with UoW
```python
def create_project(uow: ArangoUnitOfWork, name: string, path: string) -> dict:
    with uow as tx:
        project_doc = {
            "node_type": "project",
            "name": name,
            "path": path,
        }
        tx.nodes.add(NodeProposal(collection="nodes", document=project_doc))
        # Edges can be buffered later when adding folders/files
        # Commit happens automatically on context exit
    # Return freshly loaded project
    return uow.projects.get_by_name(name)
```

Checklist
- [ ] Proposal types defined
- [ ] Repositories implemented
- [ ] UoW buffers writes and commits via GraphWriter
- [ ] Services use `with uow:` pattern 