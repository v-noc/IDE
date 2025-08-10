### Collections and Registry

Registry pattern
- Central registry in `db/collections/__init__.py` exports typed collections
- One `nodes` collection using discriminated union models
- Multiple edge collections for relation kinds (belongs_to, contains, calls, uses_import, implements, virtual_contains, links_to)

Node collection
- `ArangoNodeCollection[T]` wraps a document collection with Pydantic validation
- Supports `get/create/update/delete/find/find_one/aql/truncate`
- Suggest: add `bulk_create(docs: list[T])`, `upsert`, `paginate`, `stream`

Edge collection
- `ArangoEdgeCollection[T]` ensures edge collection creation and optional unique index (via `model_config.unique_on`)
- Maps Python fields to Arango `_from`/`_to` seamlessly
- Suggest: `bulk_create`, `delete_match`, `paginate`, `traverse(start, depth, dir)` helpers

Indexes
- Apply indexes at creation:
  - Nodes: hash on `node_type`, `qname`; persistent on `properties.position.line_no` if needed
  - Edges: hash on `_from`, `_to`, `edge_type`; per-edge unique when required

API ergonomics
- Prefer bind vars everywhere; avoid string interpolation
- Return typed Pydantic models; adapters handle unions via `TypeAdapter`

Versioning
- Keep `model_version` per node/edge to enable migrations 