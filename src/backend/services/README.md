# Graph Construction Services

This directory contains the high-level services responsible for parsing source code and constructing the code graph. These services are the primary consumers of the Domain API defined in `app/core`.

## Core Components

-   **`scanner.py`**: Contains the `ProjectScanner`, which is responsible for walking the filesystem and using Python's `ast` module to parse source code into a structured format. It has no knowledge of the database or the domain objects.
-   **`builder.py`**: Contains the `GraphBuilder`, which orchestrates the entire graph construction process. It consumes the data from the `ProjectScanner` and uses the `CodeGraphManager` and domain objects to build the graph.

## Workflow and Interaction

The graph building process follows a clear, decoupled workflow:

1.  **Initiation**: An API endpoint (or a background job) decides to scan a project. It loads a `Project` domain object using the `CodeGraphManager`.
2.  **Orchestration**: The endpoint passes the `Project` object to the `GraphBuilder`'s `build_graph_for_project` method.
3.  **Scanning**:
    -   The `GraphBuilder` creates an instance of the `ProjectScanner`.
    -   It iterates through the items yielded by the scanner. The scanner yields simple Python dictionaries representing folders, files, and parsed AST data (functions, classes, imports, etc.).
4.  **Domain-Driven Construction**:
    -   For each item yielded by the scanner, the `GraphBuilder` uses the appropriate method on the `Project` domain object (or other domain objects) to add the element to the graph.
    -   For example, when the scanner yields a folder, the builder calls `project.add_folder(...)`. When it yields a function from a file, it calls `file.add_function(...)`.
5.  **Resolving Connections**:
    -   The `GraphBuilder` maintains a mapping of qualified names (qnames) to their corresponding domain objects (e.g., `{"/app/utils.py::calculate": <Function ...>}`).
    -   After initially creating all the nodes, it iterates through the collected call and import data from the scanner.
    -   It uses the map to resolve the connections. For instance, if it finds a call from `function_A` to `function_B`, it looks up both domain objects in its map and then calls `function_A.add_call(function_B, ...)`.

## Diagram of Interaction

```
+-----------------+      +----------------------+      +------------------+
|  API Endpoint   |----->|    GraphBuilder      |----->|  ProjectScanner  |
+-----------------+      +----------------------+      +------------------+
        |                        | (uses)                      | (yields)
        | (loads)                v                             v
        |              +----------------------+      +------------------+
        |              |  Domain Objects      |      |   Raw AST Data   |
        |              | (Project, File, etc.)|      |   (dicts)        |
        v              +----------------------+      +------------------+
+-----------------+              | (uses)
| CodeGraphManager|              v
+-----------------+    +----------------------+
                     |      DB Layer        |
                     |   (ORM/Collections)  |
                     +----------------------+
```

This decoupled approach makes the system highly maintainable:

-   The `scanner` can be modified to support other languages without changing the builder.
-   The `builder`'s logic is clean and readable because it operates on the high-level domain API.
-   The domain objects contain all the core business logic for how graph elements are connected, ensuring consistency.
