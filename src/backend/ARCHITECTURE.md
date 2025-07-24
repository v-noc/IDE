# Refined Backend Architecture Plan

This document outlines a refined architectural plan for the backend system. It synthesizes and improves upon the concepts from the `README-domain-api.md` and `README-graph-builder.md` files, introducing a more robust, layered architecture with a clear separation of concerns, strong typing, and a custom ORM-like abstraction for ArangoDB.

## 1. Core Principles

*   **Layered Architecture:** The system will be divided into distinct layers (ORM, Models, Domain, Services/API). Each layer has a specific responsibility and can only communicate with the layer directly below it. This reduces coupling and improves maintainability.
*   **Single Source of Truth (Models):** Pydantic models are the definitive source of truth for data structures. They are used for API validation, database serialization, and internal data transfer. They contain no business logic or database access code.
*   **Type Safety:** Leverage Python's type hints and Pydantic's validation to ensure type safety from the API layer down to the database, catching errors early and improving developer experience.
*   **Domain-Driven:** The core business logic is expressed through domain objects that represent real-world concepts (`Project`, `File`, `Function`), making the code more intuitive and readable.

## 2. Proposed Layered Architecture

```
+----------------------------------+
|      4. Services & API Layer     |  (FastAPI endpoints, GraphBuilder)
| (interacts with Domain Layer)    |
+----------------------------------+
                |
                v
+----------------------------------+
|        3. Domain Logic Layer     |  (Domain objects: Project, File, Function)
| (interacts with ORM/DB Layer)    |
+----------------------------------+
                |
                v
+----------------------------------+
|      2. Data Models (Pydantic)   |  (Pure data containers, no logic)
| (used by all layers)             |
+----------------------------------+
                |
                v
+----------------------------------+
| 1. Database Abstraction (ORM)    |  (Handles all ArangoDB communication)
+----------------------------------+
```

## 3. Detailed Component & Directory Structure

This is the target directory structure that reflects the layered architecture.

```
src/backend/app/
├── api/                  # Layer 4: API Endpoints (e.g., projects.py)
├── config/               # Application configuration
├── core/                 # Layer 3: Domain Logic
│   ├── __init__.py
│   ├── base.py           # Abstract `DomainObject` base class
│   ├── manager.py        # `CodeGraphManager` - main entry point for domain logic
│   ├── project.py        # Project domain object
│   ├── file.py           # File domain object
│   └── ...               # Other domain objects (Folder, Function, etc.)
├── db/                   # Layer 1: Database Abstraction (ORM)
│   ├── __init__.py
│   ├── client.py         # ArangoDB client setup
│   ├── orm.py            # `ArangoCollection` - The core ORM abstraction
│   └── collections.py    # Instantiated collections (nodes, edges)
├── models/               # Layer 2: Pydantic Models
│   ├── __init__.py
│   ├── base.py           # `BaseNode`, `BaseEdge` Pydantic models
│   ├── node.py           # Generic `Node` model with `node_type`
│   └── edge.py           # Generic `Edge` model with `edge_type`
└── services/             # Layer 4: Services (e.g., GraphBuilder)
    ├── __init__.py
    ├── graph_builder.py
    └── graph_scanner.py
```

### 3.1. Layer 1: The Database Abstraction (ORM)

This layer provides a clean, typed, and consistent API for all database interactions, abstracting away the `python-arango` driver.

**`db/orm.py` - `ArangoCollection`**

This generic class will manage operations for a single ArangoDB collection.

```python
# Pseudocode for db/orm.py
from typing import Type, TypeVar, Generic
from pydantic import BaseModel
from arango.collection import StandardCollection

T = TypeVar('T', bound=BaseModel)

class ArangoCollection(Generic[T]):
    def __init__(self, collection: StandardCollection, model: Type[T]):
        self._collection = collection
        self._model = model

    def get(self, key: str) -> T | None:
        # Fetches a document and validates it with the Pydantic model
        ...

    def create(self, doc_data: T) -> T:
        # Inserts a new document, returning the stored, validated model
        ...

    def update(self, key: str, patch_data: BaseModel) -> T:
        # Updates a document and returns the new, validated model
        ...

    def delete(self, key: str) -> bool:
        ...

    def find(self, filters: dict, limit: int = 10) -> list[T]:
        # Finds documents using AQL
        ...
```

**`db/collections.py` - Collection Instances**

This file will provide singleton instances of `ArangoCollection` for the rest of the app to use.

```python
# Pseudocode for db/collections.py
from .orm import ArangoCollection
from ..models import node, edge
from .client import db # ArangoDB client

# Node Collections
nodes = ArangoCollection[node.Node](db.collection('nodes'), node.Node)

# Edge Collections
contains_edges = ArangoCollection[edge.ContainsEdge](db.collection('contains'), edge.ContainsEdge)
calls_edges = ArangoCollection[edge.CallEdge](db.collection('calls'), edge.CallEdge)
# ... and so on for all edge types
```

### 3.2. Layer 2: Pydantic Models

Models will be refactored into pure data containers with no database logic.

**`models/base.py`**

```python
# Pseudocode for models/base.py
from pydantic import BaseModel, Field

class ArangoBase(BaseModel):
    key: str | None = Field(None, alias='_key')
    id: str | None = Field(None, alias='_id')

class BaseNode(ArangoBase):
    node_type: str

class BaseEdge(ArangoBase):
    from_id: str = Field(..., alias='_from')
    to_id: str = Field(..., alias='_to')
    edge_type: str
```

### 3.3. Layer 3: The Domain Logic Layer

This is where the application's business logic resides. Domain objects wrap Pydantic models and use the ORM layer to perform actions.

**`core/base.py` - `DomainObject`**

An abstract base class to provide common functionality to all domain objects.

```python
# Pseudocode for core/base.py
from typing import TypeVar, Generic
from ..models.base import ArangoBase

M = TypeVar('M', bound=ArangoBase)

class DomainObject(Generic[M]):
    def __init__(self, model: M):
        self.model = model

    @property
    def id(self) -> str:
        return self.model.id

    @property
    def key(self) -> str:
        return self.model.key
```

**`core/file.py` - Example Domain Object**

```python
# Pseudocode for core/file.py
from .base import DomainObject
from ..models import node, edge
from ..db import collections as db
from .function import Function # Another domain object

class File(DomainObject[node.FileNode]):
    def add_function(self, name: str, ...) -> Function:
        # 1. Create the Pydantic model for the function node
        func_model = node.FunctionNode(name=name, ...)

        # 2. Use the ORM to save the node
        created_func_model = db.nodes.create(func_model)

        # 3. Create the Pydantic model for the edge
        contains_edge_model = edge.ContainsEdge(
            _from=self.id,
            _to=created_func_model.id
        )

        # 4. Use the ORM to save the edge
        db.contains_edges.create(contains_edge_model)

        # 5. Return the new Function domain object
        return Function(created_func_model)
```

## 4. Refactoring and Implementation Steps

1.  **Create New Directory Structure:** Create the new directories (`core`, `services`) and move existing files to match the new structure.
2.  **Implement the ORM:**
    *   Create `db/orm.py` with the generic `ArangoCollection` class.
    *   Create `db/collections.py` and instantiate the collection managers.
3.  **Refactor Models:**
    *   Create `models/base.py` with `ArangoBase`, `BaseNode`, and `BaseEdge`.
    *   Ensure all specific node and edge models in `models/` inherit from these base models and contain only data fields.
4.  **Implement Domain Layer:**
    *   Create `core/base.py` with the `DomainObject` base class.
    *   Refactor existing domain logic (`Project`, `File`, etc.) into classes in the `core/` directory, making them inherit from `DomainObject` and use the new ORM (`db.collections`).
5.  **Update Service & API Layers:**
    *   Refactor the `GraphBuilder` (now in `services/`) to use the new Domain Layer or ORM layer.
    *   Refactor the API endpoints in `api/` to exclusively call methods on the `CodeGraphManager` and other domain objects.
6.  **Cleanup:** Remove old database access patterns and redundant code.
7.  **Update Tests:** Adapt all tests to the new architecture, ensuring each layer is tested appropriately.
