### Models: Composition and Inheritance

Principles
- Prefer composition (separate `properties` per node) for flexibility
- Use inheritance for shared base fields (`ArangoBase`, `BaseNode`, `BaseEdge`)
- Discriminated unions to validate diverse node types in a single collection

Structure
- Base models: `ArangoBase` (key/id), `BaseNode` (node_type), `BaseEdge` (_from/_to, edge_type)
- Node types: `ProjectNode`, `FolderNode`, `FileNode`, `FunctionNode`, `ClassNode`, `PackageNode`, `VirtualFolderNode`, `VirtualFileNode`
- Properties: `ProjectProperties`, `FileProperties`, `FunctionProperties`, `ClassProperties`, etc.

Composition patterns
- Keep base node minimal; put specifics in `properties` to avoid schema churn
- Enrich domain behavior via wrappers (e.g., `Project`, `VirtualFolder`) rather than fat models

Inheritance patterns
- Introduce abstract mixins sparingly (e.g., `Positioned` for nodes with source spans)
- For edges, allow `unique_on` in `model_config` for constraints

Validation and defaults
- Provide strict `Field(..., description=...)` for critical fields
- Use factories for list defaults (`default_factory=list`)

Versioning and compatibility
- `model_version` field; migration scripts upgrade stored docs to the latest 