### SymbolIndex: Indexing and Resolution

#### Goals
- Fast, accurate resolution across modules, types, functions, and packages
- Clear separation of concerns and explicit kinds
- Thread-safe and versioned for incremental builds

#### Data structures
- Maps by kind:
  - modules: Map<qname, id>
  - classes: Map<qname, id>
  - functions: Map<qname, id>
  - packages: Map<qname, id>
- Imports per file: Map<fileId, Map<alias, qname>>
- Module trie (prefix tree) for module path lookups
- Reverse import graph: Map<moduleQname, Set<dependentModuleQname>>

#### QName rules
- module qname: project-root-relative path with dots (no .py)
- symbol qname: module qname + nested scopes joined by dots

#### Resolution algorithms
- Resolve import alias → qname
  - O(1) via `imports[fileId][alias]`
- isLocalModule(qname)
  - true if `modules.has(qname)` or if a prefix of qname exists in modules
- Resolve function by simple name inside file
  - `qname = fileModule + '.' + name`; check functions
- Resolve attribute call module.function
  - if `imports[fileId][moduleAlias] = moduleQname`, then `moduleQname + '.' + fn`
- Resolve class/constructor
  - check `classes` for `fileModule + '.' + name`, then `classes[name]`

#### Packages vs local modules
- Prefer explicit package index
  - If `modules.has(prefix)` → local
  - Else consult package index (created on demand) → external
- When encountering `foo.bar` unresolved:
  - If `modules.has(foo)` → local package/module
  - Else create/get package node for `foo` and record in `packages`

#### Concurrency & versioning
- Staged commits: Stage 1 builds a next-version index snapshot, then swaps
- Readers (Stage 2 workers) hold a snapshot handle

#### Persistence & caching
- Persist `modules`, `classes`, `functions` with stable IDs
- Cache contents keyed by project + index version
- Store file content-hash to skip unchanged files

#### API sketch
- See `symbol-table/API_SPEC.md` 