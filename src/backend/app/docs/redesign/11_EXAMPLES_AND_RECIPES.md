### 11. Examples and Recipes

Create a project (write path)
```python
uow = uow_factory()
with uow:
  project = Project.create(name, path)
  uow.projects.add(project)
  uow.commit()
```

List projects (read path)
```python
projects = project_read_repo.list(offset=0, limit=20)
```

Add file and link contains edge
```python
with uow:
  folder = uow.folders.get(folder_id)
  file = File.create(name, qname, path)
  folder.add_child(file)
  uow.nodes.add(file)
  uow.edges.add(ContainsEdge.from_parent_child(folder.id, file.id, position))
  uow.commit()
```

Bulk write
```python
with uow:
  uow.nodes.bulk_add(files)
  uow.edges.bulk_add(edges)
  uow.commit()
``` 