# ArangoDB Schema and Model Refactoring Plan

This document outlines a plan to refactor the ArangoDB schema, models, and associated database logic for improved clarity, consistency, and maintainability.

## 1. Analysis of Current Structure

The existing structure has several areas for improvement:

- **Model Duplication:** There are conflicting and duplicated models for `Project` and `Node` (e.g., `models/project.py` vs. `models/projects/projects.py`). This creates ambiguity.
- **Inconsistent Naming:** Naming for files, classes, and fields is inconsistent. For example, some edge models are named with a `Node` suffix (e.g., `CallNode`), which is misleading.
- **Overly Fragmented Structure:** The `models/Node` directory is highly fragmented, making it difficult to get a clear overview of the graph schema. Edge and node definitions are mixed inconsistently.
- **Unclear Relationships:** The purpose of the generic `Connection` edge is unclear when more specific edges like `Contains` and `Call` exist.

## 2. Proposed New Structure

To address these issues, we propose the following restructured and simplified `models` directory.

### 2.1. New `models` Directory Structure

```
src/backend/app/
├── models/
│   ├── __init__.py
│   ├── base.py           # (No change) BaseDocument and BaseEdge
│   ├── project.py        # Consolidated Project document model
│   ├── node.py           # Consolidated Node document model (with NodeType enum)
│   └── edges.py          # All edge models in one file for clarity
└── db/
    ├── __init__.py
    ├── client.py         # (No change)
    ├── orm.py            # (No change)
    ├── service.py        # (Will be updated for new managers)
    ├── dependencies.py   # (No change)
    └── collections/
        ├── __init__.py
        ├── projects.py     # Manager for the 'projects' collection
        ├── nodes.py        # Manager for the 'nodes' collection
        └── (edge managers) # Managers for each edge collection
```

### 2.2. Proposed Collections and Edges

We will use the following collections:

**Document Collections:**

- `projects`: Stores project documents. Each project is the root of a graph.
- `nodes`: Stores all node documents, regardless of their type. A `node_type` field will differentiate them.

**Edge Collections:**

- `ContainsEdge`: Represents containment relationships (e.g., a folder containing a file, a file containing a function). Replaces `ContainsNode` and `ContainsFilesOrFolder`.
- `CallEdge`: Represents a function or schema call. Replaces `CallNode`.
- `ImportEdge`: Represents an import statement. Replaces `ImportNode`.
- `BelongsToEdge`: A new edge to link nodes to a project. This is more explicit than embedding `project_key` in each node.

## 3. Model Consolidation and Renaming

### 3.1. `project.py`

- The two `Project` models will be merged into a single `app/models/project.py`.
- It will be the definitive model for a project document.

```python
# src/backend/app/models/project.py
from .base import BaseDocument

class Project(BaseDocument):
    name: str
    description: str
    path: str
```

### 3.2. `node.py`

- All node types will be consolidated into a single `app/models/node.py`.
- The `NodeType` enum will be used to distinguish between different types of nodes.
- Specific node attributes can be stored in a flexible `properties` dictionary.

```python
# src/backend/app/models/node.py
from enum import Enum
from .base import BaseDocument
from pydantic import Field, BaseModel
from typing import Any, Dict, List

class NodeType(str, Enum):
    PROJECT = "project"
    FOLDER = "folder"
    FILE = "file"
    FUNCTION = "function"
    CLASS = "class" # Renamed from SCHEMA for clarity
    IMPORT = "import"

class NodePosition(BaseModel):
    line_no: int
    col_offset: int
    end_line_no: int
    end_col_offset: int

class Node(BaseDocument):
    node_type: NodeType = Field(..., description="The type of the node.")
    name: str = Field(..., description="The name of the node (e.g., function name, file name).")
    qname: str = Field(..., description="The fully qualified name of the node.")
    properties: Dict[str, Any] = Field(default_factory=dict, description="A dictionary of arbitrary properties for the node.")

```

### 3.3. `edges.py`

- All edge models will be defined in `app/models/edges.py`.
- Class names will be suffixed with `Edge` for clarity.

```python
# src/backend/app/models/edges.py
from .base import BaseEdge
from .node import NodePosition
from pydantic import Field

class BelongsToEdge(BaseEdge):
    """Links a node to a project."""
    pass

class ContainsEdge(BaseEdge):
    """Represents that a node is contained within another (e.g., file in a folder)."""
    position: NodePosition = Field(..., description="The position of the contained node.")

class CallEdge(BaseEdge):
    """Represents a call from one node to another (e.g., function call)."""
    position: NodePosition = Field(..., description="The position of the call in the source code.")

class ImportEdge(BaseEdge):
    """Represents an import statement."""
    alias: str | None = None
    position: NodePosition = Field(..., description="The position of the import statement.")
```

## 4. Refactoring Steps

1.  **Create New Files:** Create the new directory structure and files (`models/node.py`, `models/project.py`, `models/edges.py`).
2.  **Populate New Models:** Add the consolidated code to the new model files.
3.  **Delete Old Files:** Remove the old `models/Node`, `models/projects`, `models/node.py`, `models/project.py`, and `models/connection.py` files and directories.
4.  **Update DB Managers:**
    - Create new manager files in `db/collections/` for the new edge collections (`contains.py`, `calls.py`, etc.).
    - Update `db/collections/nodes.py` and `db/collections/projects.py` to use the new consolidated models.
    - Update `db/service.py` to instantiate the new managers.
5.  **Update API Endpoints:** Refactor any API endpoints that use the old models to use the new, consolidated models.
6.  **Update Tests:** Update any tests to reflect the changes in the models and database layer.

This refactoring will result in a much cleaner, more understandable, and more maintainable codebase.
