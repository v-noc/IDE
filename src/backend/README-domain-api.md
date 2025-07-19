# Domain-Centric Graph API Plan

This document outlines a plan to create a high-level, domain-centric API for interacting with the code graph. This API will abstract away the raw node and edge creation, providing a more intuitive and readable way to build and modify the representation of a codebase.

## 1. Goal

The goal is to create a Domain-Specific Language (DSL) for the code graph. Instead of manually creating nodes and linking them with edges, developers will interact with domain objects that have methods reflecting the real-world structure of code.

-   **Before (Low-Level):**
    ```python
    file_node = node_factory.create_file_node(...)
    db.nodes.create(file_node)
    func_node = node_factory.create_function_node(...)
    db.nodes.create(func_node)
    edge = edge_factory.create_contains_edge(file_node._id, func_node._id, ...)
    db.contains.create(edge)
    ```
-   **After (High-Level Domain API):**
    ```python
    my_project = code_graph_manager.load_project("my_project_key")
    my_file = my_project.add_file("/path/to/file.py")
    my_function = my_file.add_function("my_func", ...)
    my_function.add_call(another_function, ...)
    ```

## 2. Proposed Directory Structure

A new `domain` directory will be created to house this abstraction layer.

```
src/backend/app/
├── domain/
│   ├── __init__.py
│   ├── manager.py        # Central entry point: CodeGraphManager
│   ├── project.py        # The Project domain class
│   ├── container.py      # Base class for things that contain other elements (Project, Folder, File)
│   ├── file.py           # The File domain class
│   ├── folder.py         # The Folder domain class
│   └── code_elements.py  # Domain classes for Function, Class, Import
└── graph/
    └── ... (The lower-level builder, which can still be used for initial bulk scanning)
```

## 3. Core Components

### 3.1. `manager.py` - The `CodeGraphManager`

-   **Responsibility:** Acts as the main entry point for all domain interactions.
-   **Methods:**
    -   `create_project(name, path, ...)`: Creates a new project and returns a `Project` domain object.
    -   `load_project(project_key)`: Loads an existing project from the database and returns a hydrated `Project` domain object.

### 3.2. Domain Object Classes (`Project`, `Folder`, `File`, `Function`, etc.)

-   **Core Principle:** Each class will wrap a `Node` Pydantic model. It will hold the node's data and a reference to the `db_service` to perform actions.
-   **Example: `File` domain object in `file.py`**
    -   `__init__(self, node_data: Node, db_service: DatabaseService)`
    -   `add_function(name, position, ...)`:
        1.  Creates a `FUNCTION` node using the `NodeFactory`.
        2.  Saves it to the database via `db_service`.
        3.  Creates a `ContainsEdge` linking the file to the new function.
        4.  Saves the edge to the database.
        5.  Returns a `Function` domain object.
    -   `add_class(name, position, ...)`: Similar to `add_function`.
    -   `get_functions()`: Queries the database for all `FUNCTION` nodes contained within this file and returns a list of `Function` domain objects.

### 3.3. `container.py` - Base Class for Containers

-   To avoid code duplication, a `Container` base class can be created.
-   `Project`, `Folder`, and `File` all act as containers.
-   This class can provide shared logic for adding and retrieving elements. For example, a generic `_add_element(node_type, ...)` method.

## 4. Refactoring and Implementation Steps

1.  **Create New Files:** Create the `domain` directory and the files outlined above.
2.  **Implement `CodeGraphManager`:** Create the manager class with `create_project` and `load_project` methods.
3.  **Implement Domain Classes:**
    -   Start with `Project` in `project.py`.
    -   Implement `Folder` and `File`.
    -   Implement `Function`, `Class`, and `Import` in `code_elements.py`.
4.  **Move Logic from Factories/Builder:** The high-level logic for connecting nodes (e.g., a file containing a function) will be moved from the `GraphBuilder` into the methods of these domain objects. The `NodeFactory` and `EdgeFactory` will become simple, stateless helper classes used by the domain objects.
5.  **Update API Endpoints:** The API endpoints in `api/projects.py` can be refactored to use the new `CodeGraphManager`. This will make the API code much cleaner and more readable.
6.  **Update Tests:** Create new tests specifically for the domain API to ensure its correctness.
