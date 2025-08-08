### Examples

Create a project
```python
from app.core.manager import CodeGraphManager
mgr = CodeGraphManager()
proj = mgr.create_project(name="myproj", path="/abs/path")
```

Create and link nodes/edges directly
```python
from app.db import collections as db
from app.models.node import FileNode
from app.models.properties import FileProperties

file_node = FileNode(name="main.py", qname="pkg.main", node_type="file", properties=FileProperties(path="/abs/pkg/main.py"))
created = db.nodes.create(file_node)
```

Find related nodes via traversal
```python
related = db.nodes.find_related(start_node_id=created.id, edge_collection=db.contains_edges, direction="outbound", limit=3)
```

AQL with bind vars
```python
rows = db.nodes.aql("""
FOR doc IN nodes
  FILTER doc.node_type == @type
  RETURN doc
""", {"type": "file"})
```

Bulk create (proposed)
```python
files = [FileNode(...), FileNode(...)]
created = db.nodes.bulk_create(files)
``` 