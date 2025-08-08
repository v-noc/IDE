### Identifiers, QNames, and Invariants

Identifiers
- Node `_id` and `_key` managed by ArangoDB
- Stable logical identity via `qname` for code elements; optional uniqueness

Invariants
- `contains` must be acyclic
- Virtual folders cannot link to other virtual folders as targets
- `links_to` must be unique per virtual folder to element

Consistency
- Prefer eventual consistency for expensive checks; background validators
- Use versioning on aggregates for optimistic concurrency 