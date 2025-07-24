# Database Abstraction Layer (ORM)

This directory contains the application's database abstraction layer, which acts as a lightweight, typed Object-Relational Mapper (ORM) for ArangoDB. It ensures that all database interactions are consistent, validated, and decoupled from the application's business logic.

## Core Components

-   **`client.py`**: Sets up and provides a singleton instance of the `python-arango` database client.
-   **`orm.py`**: Contains the `ArangoCollection` class, the heart of the ORM.
-   **`collections.py`**: Provides pre-configured, singleton instances of `ArangoCollection` for every node and edge collection in the database.

## The `ArangoCollection` Class

The `ArangoCollection` is a generic class that wraps a specific ArangoDB collection and binds it to a Pydantic model. It provides standard CRUD (Create, Read, Update, Delete) operations that automatically handle data validation.

### Example Usage

Instead of interacting with the database driver directly, you use the instances from `db.collections`.

```python
# In some domain logic file...
from ..db import collections as db
from ..models import node, properties

# Creating a new node
new_file_node = node.FileNode(
    name="main.py",
    qname="/app/main.py",
    node_type="file",
    properties=properties.FileProperties(path="/app/main.py")
)
# The .create() method automatically validates the input and returns
# the database-created document, also validated against the model.
created_node = db.nodes.create(new_file_node)

# Retrieving a node
retrieved_node = db.nodes.get("my-node-key")
if retrieved_node:
    print(f"Found node: {retrieved_node.name}")
```

## Extending the ORM with Custom Queries

While the base `ArangoCollection` provides common methods like `find` and `get`, you will often need more complex, collection-specific queries (e.g., graph traversals).

There are two primary ways to add custom queries:

### 1. Global Queries (Inside `ArangoCollection`)

If a query is generic enough to be useful for **any** collection, you can add it directly to the `ArangoCollection` class in `orm.py`. The `aql` method is a good example of this.

### 2. Collection-Specific Queries (Recommended)

For queries that are specific to a certain collection (e.g., finding all methods implemented by a class), the best practice is to create a new class that **inherits** from `ArangoCollection` and add your custom methods there.

Then, update `db/collections.py` to use your new, extended class.

#### Example: Adding a `find_by_qname` method for nodes

**Step 1: Create a custom collection class.**

```python
# in db/orm.py (or a new file, e.g., db/custom_collections.py)

from .orm import ArangoCollection
from ..models import node

class NodeCollection(ArangoCollection[node.Node]):
    
    def find_by_qname(self, qname: str) -> node.Node | None:
        """Finds a node by its fully qualified name."""
        results = self.find({"qname": qname}, limit=1)
        return results[0] if results else None

    def find_functions_in_file(self, file_id: str) -> list[node.FunctionNode]:
        """Finds all functions contained within a specific file."""
        query = """
        FOR func IN 1..1 OUTBOUND @file_id contains
            FILTER func.node_type == 'function'
            RETURN func
        """
        bind_vars = {"file_id": file_id}
        cursor = self.db.aql.execute(query, bind_vars=bind_vars)
        # Ensure you validate the results against the correct model
        return [node.FunctionNode.model_validate(doc) for doc in cursor]
```

**Step 2: Update `db/collections.py` to use it.**

```python
# in db/collections.py

# from .orm import ArangoCollection # Old
from .orm import NodeCollection # New
from ..models import node, edges

# Use the new NodeCollection class instead of the generic one
nodes = NodeCollection(
    collection_name="nodes",
    model=node.Node
)

# Other collections can still use the base class
calls_edges = ArangoCollection[edges.CallEdge](...)
```
