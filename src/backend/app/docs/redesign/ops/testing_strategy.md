### Testing Strategy

Pyramids
- Unit tests for domain logic (no db)
- Integration tests for repositories and GraphWriter
- E2E tests for API routes and flows

Guidelines
- Use factories/builders for nodes/edges
- Mock Arango at boundaries only in unit tests
- Prefer real db for integration with rollback fixtures

## Step-by-step: Example tests

1) Unit test (domain)
```python
def test_project_emits_contains_edge():
    project = Project({"_id": "nodes/1", "_key": "1", "name": "demo"})
    project.add_virtual_folder("nodes/f1")
    edges = project.collect_edges()
    assert any(e.collection == "contains" and e.to_id == "nodes/f1" for e in edges)
```

2) Integration test (GraphWriter)
```python
def test_graph_writer_upserts_nodes_and_edges(db):
    writer = ArangoGraphWriter(db)
    nodes = [NodeProposal(collection="nodes", document={"qname": "demo::API", "node_type": "virtual_folder"})]
    edges = [EdgeProposal(collection="contains", from_id="nodes/1", to_id="nodes/2")]
    writer.write(nodes, edges)
    assert db.nodes.find_one({"qname": "demo::API"}) is not None
``` 