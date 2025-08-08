### 03. Graph Schema and Indices

Collections
- nodes (document): discriminated union by `node_type`
- belongs_to, contains, virtual_contains, calls, uses_import, implements, links_to (edge)

Indexes (create once on startup)
- nodes
  - hash: `node_type`
  - hash: `qname` (unique optional)
  - persistent: `properties.position.line_no` (optional)
- edges (each collection)
  - hash: `_from`
  - hash: `_to`
  - hash: `edge_type` (optional; constant but helps filters across joins)
  - unique: per collection as needed (e.g., links_to unique on `_from`)

Named graph (optional)
- Define Arango Graph for key traversals (contains + belongs_to) to optimize path queries

Conventions
- Always store minimal shape; avoid denormalizing unless justified by read perf
- Use bind vars; never interpolate

Referential integrity
- Option A: validate endpoints on write (extra read cost)
- Option B: write fast and validate asynchronously (background job) 