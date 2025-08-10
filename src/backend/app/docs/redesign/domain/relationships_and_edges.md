### Relationships & Edge Semantics

Edge taxonomy
- belongs_to: child → parent ownership
- contains: container → content structural relation
- virtual_contains: virtual folder → child (virtual or code)
- calls: function → function
- uses_import: element → package
- implements: class → interface/abstract (future)
- links_to: virtual folder → code element direct link

Edge metadata
- `edge_type` field for cross-collection filtering
- `call_order` for virtual paths
- Timestamps and actor metadata optional for auditing

API contracts
- Domain returns EdgeProposals: `{ from_id, to_id, edge_type, props }`
- GraphWriter resolves and persists with idempotency

## Step-by-step: Produce and persist edges

1) Produce edges in domain
```python
edges = [
  EdgeProposal(collection="contains", from_id=project.id, to_id=folder.id),
  EdgeProposal(collection="links_to", from_id=folder.id, to_id=function.id, props={"call_order": 1}),
]
```

2) Persist via UoW
```python
uow.edges.add_many(edges)
``` 