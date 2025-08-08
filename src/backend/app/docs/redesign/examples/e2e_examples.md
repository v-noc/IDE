### End-to-End Examples

Goal
- Create a project, add a virtual folder, link a function, and query it back

Prerequisites
- `ArangoUnitOfWork` and `ArangoGraphWriter` implemented
- Repositories wired inside UoW

## Step-by-step

1) Create a project
```python
service.create(CreateProjectCommand(name="demo", path="/tmp/demo"))
```

2) Add a virtual folder under the project
```python
with uow_factory() as uow:
    project = uow.projects.get_by_name("demo")
    folder_doc = {"node_type": "virtual_folder", "name": "API", "qname": "demo::API"}
    uow.nodes.add(NodeProposal(collection="nodes", document=folder_doc))
    # link project → folder
    uow.edges.add_many([
        EdgeProposal(collection="contains", from_id=project["_id"], to_id=f"nodes/{'api_key'}")
    ])
```

3) Link a function to the virtual folder
```python
func = uow.nodes.get_by_qname("app.services.user.get_user")
uow.edges.add_many([
    EdgeProposal(collection="links_to", from_id=f"nodes/{'api_key'}", to_id=func["_id"])
])
```

4) Query virtual folders with pagination
```python
AQL = """
FOR v IN nodes
  FILTER v.node_type == "virtual_folder" && LIKE(v.qname, @prefix, true)
  LIMIT @offset, @limit
  RETURN { key: v._key, name: v.name, qname: v.qname }
"""
result = db.aql.execute(AQL, bind_vars={"prefix": "demo::%", "offset": 0, "limit": 20})
```

5) Verify edges exist
```aql
FOR e IN contains FILTER e._from == @project_id RETURN e
FOR e IN links_to FILTER e._from == @folder_id RETURN e
```

Tips
- Keep writes idempotent
- Use DTOs at boundaries and map to domain 