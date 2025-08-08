### SymbolIndex API Spec

#### Mutations
- addModule(qname: string, id: string)
- addClass(qname: string, id: string)
- addFunction(qname: string, id: string)
- addPackage(qname: string, id: string)
- addImport(fileId: string, alias: string, qname: string)

#### Queries
- resolve(kind: 'module'|'class'|'function'|'package', qname: string): string | null
- isKnown(kind: 'module'|'class'|'function'|'package', qname: string): boolean
- isLocalModule(qname: string): boolean
- getImports(fileId: string): Record<string, string>
- getDependents(moduleQname: string): string[]

#### Snapshots & concurrency
- openSnapshot(): SymbolIndexSnapshot
- commitStaged(staged: SymbolIndexStaged): versionId
- withSnapshot<T>(fn: (snap: SymbolIndexSnapshot) => T): T

#### Diagnostics
- debug(): { counts, sampleEntries }
- metrics(): { hits, misses, versions }

#### Notes
- All mutation APIs are disabled on snapshots; use staged builder in Stage 1.
- IDs are storage IDs (graph DB) or stable logical IDs in offline mode. 