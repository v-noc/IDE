### Pipeline and Contracts

#### Stages
- Discovery → files
- Stage 1: DeclarationPass(file) → DeclarationResult
- Index barrier: SymbolIndex.commit(modules/types/functions)
- Stage 2: DetailPass(file, SymbolIndex) → DetailResult
- Persist: GraphWriter.bulkCommit(nodes, edges, updates)
- Reporting: aggregate Issues + Metrics

#### DeclarationResult
- nodes: [Module|Class|Function]
- parentOf: { childQname → parentQname | undefined }
- issues: Issue[]

#### DetailResult
- edges: [UsesImportEdge|CallEdge|ContainsEdge]
- typeFacts: [TypeFact]
- cfg: ControlFlowGraph | null
- issues: Issue[]

#### Issue
- code: string (e.g., LEX1001, PAR2001, RES3001)
- severity: info|warning|error
- file: path
- span: { line, col, endLine, endCol }
- message: string

#### TypeFact
- subjectQname: string
- fact: one of
  - functionReturnType: string
  - variableType: { name: string, type: string }
  - classFieldType: { name: string, type: string }
  - aliasType: { alias: string, type: string }

#### SymbolIndex contract
- addModule(qname, id)
- addClass(qname, id)
- addFunction(qname, id)
- addPackage(qname, id)
- resolve(kind, qname) → id | null
- isKnown(kind, qname) → boolean
- getImports(fileId) → { alias → qname }

#### GraphWriter contract
- bulkCreateNodes(nodes)
- bulkCreateEdges(edges)
- bulkUpdateProperties(updates)
- transactional boundaries per file or batch-size 