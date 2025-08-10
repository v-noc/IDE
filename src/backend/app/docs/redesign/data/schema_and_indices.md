### Graph Schema & Indices

Collections
- `nodes` (document): discriminated union by `node_type`
- Edge collections: `belongs_to`, `contains`, `virtual_contains`, `calls`, `uses_import`, `implements`, `links_to`

Indices
- nodes
  - hash: `node_type`
  - hash: `qname` (unique optional)
  - persistent: `properties.position.line_no` (optional)
- edges (each collection)
  - hash: `_from`
  - hash: `_to`
  - hash: `edge_type` (optional)
  - unique: per collection as needed (e.g., `links_to` unique on `_from`)

Named graph
- Define named graph for `contains` + `belongs_to` traversals
- Benefits: optimized traversals, simpler AQL

Conventions
- Minimal stored shape; avoid denormalization
- Bind variables only; no string interpolation
- Soft deletes via `properties.deleted_at` (optional)

Referential integrity
- Option A: validate endpoints on write (extra read)
- Option B: write fast; async validator job scans and fixes

## Step-by-step: Define schema with AQL examples

1) Create indices
```aql
// nodes
CREATE INDEX idx_nodes_node_type ON nodes(node_type) TYPE hash
CREATE INDEX idx_nodes_qname ON nodes(qname) TYPE hash UNIQUE

// edges
FOR col IN ["contains", "belongs_to", "calls", "uses_import", "links_to", "virtual_contains"]
  LET _ = (
    CREATE INDEX CONCAT("idx_", col, "__from") ON @@col(_from) TYPE hash OPTIONS { sparse: false }
  )
  RETURN col
```

2) Document shapes
```json
{
  "_key": "123",
  "node_type": "function",
  "name": "get_user",
  "qname": "app.services.user.get_user",
  "properties": {
    "position": { "line_no": 10, "col_offset": 0 }
  }
}
```

3) Edge upsert example
```aql
UPSERT { _from: @from, _to: @to }
INSERT { _from: @from, _to: @to, edge_type: "contains" }
UPDATE { edge_type: "contains" } IN contains
``` 