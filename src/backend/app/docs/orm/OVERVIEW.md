### ORM & Graph: Overview

Goals
- Well-structured, scalable ArangoDB ORM layer
- Clear separation between models (Pydantic), collections (CRUD), domain services (e.g., `CodeGraphManager`)
- Composition-first, inheritance when beneficial
- Batch-friendly, testable, and modular across features

Layering
- Models: Pydantic `Node` and `Edge` families, `properties/*`
- Collections (ORM): `ArangoNodeCollection`, `ArangoEdgeCollection`, central registry in `db/collections`
- Domain: wrappers (`Project`, `VirtualFolder`, etc.) orchestrated by `CodeGraphManager`
- Application: API routes use domain services

Data model
- Single `nodes` collection with discriminated union on `node_type`
- Multiple edge collections per relation kind (contains, calls, uses_import, etc.)
- Rich `properties` per node type; keep base fields small, properties detailed

Execution flow
- API/domain creates Pydantic models → ORM persists → domain wraps returned models
- Queries use AQL with bind vars; traversals through edge collections

Key design choices
- Discriminated unions reduce collection sprawl
- Edge collections per relation improve clarity and indexing
- Adapter-style ORM: typed wraps around Arango client with Pydantic validation 