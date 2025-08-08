### 02. Domain Modeling

Aggregates
- Project (root): contains Folders/Files; owns Virtual roots
- Folder/File (structure): contain Functions/Classes; belong to Project
- Function/Class (code): own type info, call edges
- Package (external): references imports, version/source metadata
- VirtualFolder/File (organization): link to code elements

Composition-first
- Keep BaseNode minimal; move specifics to properties value objects
- Domain wrappers expose behavior (e.g., `Project.add_file`, `Folder.add_function`)
- Avoid fat inheritance hierarchies; use mixins for cross-cutting concerns (e.g., `Positioned`)

Identifiers and qnames
- Stable `_id` from Arango; `qname` for logical identity
- Aggregate root methods accept value objects (properties) to avoid leaking persistence concerns

Relationships
- Use explicit edge types for semantics: belongs_to, contains, calls, uses_import, implements, links_to, virtual_contains
- Domain methods create intents (EdgeProposals); persistence layer realizes them

Validation
- Pydantic for DTOs; domain layer enforces invariants (e.g., no cycles in contains)

Versioning
- `model_version` per node/edge; migration aware 