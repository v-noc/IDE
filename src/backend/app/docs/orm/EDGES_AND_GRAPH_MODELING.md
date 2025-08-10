### Edges and Graph Modeling

Edge taxonomy (current)
- belongs_to: node → project
- contains: parent → child (with `position` for order/spans)
- virtual_contains: virtual hierarchy
- calls: function → function/method (with order, position)
- uses_import: consumer → provider (with positions)
- implements: class → method (optional)
- links_to: virtual container → code element (unique on `_from`)

Design tips
- Keep one semantic per edge collection → clean indexes and traversals
- Store minimal denormalized info on edges when it helps filtering (e.g., `edge_type` already present)
- Use unique constraints where multiplicity must be 1:1 (e.g., `links_to` for `_from`)

Traversals
- Outbound/Inbound/Any over specific collections
- Limit depth for performance; parameterize bounds
- Provide helpers in node ORM: `find_related`, `get_all_descendants`

Graph shapes
- Project tree: `belongs_to`, `contains`
- Code semantics: `uses_import`, `calls`, `implements`
- Virtual organization: `virtual_contains`, `links_to`

Consistency
- Validate `_from` and `_to` existence before write (optional), or allow lazy and report missing during reads

Caching
- Cache hot traversals (e.g., descendants) keyed by root and collection 