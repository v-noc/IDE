### Concurrency, Scaling, and Bulk Operations

Concurrency
- Optimistic concurrency with version fields on aggregates
- Retry policies for transient Arango errors
- Per-request Unit of Work enforcing single-writer per aggregate

Bulk
- GraphWriter bulk upserts for nodes/edges
- Idempotent operations: unique constraints (e.g., links_to `_from`)
- Back-pressure: queue bulk jobs; chunk writes

Scaling
- Separate read replicas (Foxx/Views) for analytical queries
- Split heavy traversals into stages; cache intermediate projections
- Use named graphs for core traversals (contains/belongs_to)

Throughput
- Avoid N+1 AQL by projecting required fields
- Prefer pagination cursors over offsets 