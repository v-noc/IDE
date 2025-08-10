### 05. Module Boundaries and Package Layout

Suggested layout
- app/
  - api/
  - application/  (services: commands, queries)
  - domain/
    - projects/
    - code/
    - virtual/
    - shared/
  - infrastructure/
    - db/
      - client.py
      - collections/
      - repositories/ (node_repo.py, edge_repo.py, project_repo.py)
      - uow.py, graph_writer.py
    - logging/, metrics/
  - docs/

Rules
- application depends on domain and infrastructure abstractions (interfaces)
- domain has no dependency on infrastructure
- API depends on application

Benefits
- Modularity, testability, parallel development by context 