# Graph Builder and Validation System Plan

This document outlines the plan for creating a modular system to build, connect, and validate the ArangoDB graph representation of a source code project.

## 1. Goal

The goal is to create a robust system that can:
1.  Scan a project directory.
2.  Parse source code files to identify key elements (classes, functions, imports, etc.).
3.  Use the refactored ArangoDB models to create a corresponding graph.
4.  Encapsulate the logic for how different code elements are connected.
5.  Provide validation to ensure the graph's integrity.

## 2. Proposed Directory Structure

All new logic will be housed within a new `graph` directory inside `app`.

```
src/backend/app/
├── graph/
│   ├── __init__.py
│   ├── builder.py        # The main GraphBuilder service.
│   ├── factories.py      # Factories for creating Node and Edge objects.
│   ├── scanner.py        # Logic for scanning the filesystem and parsing files (e.g., using AST).
│   └── validator.py      # Logic for validating the integrity of the graph.
├── models/
│   └── ... (existing refactored models)
���── db/
    └── ... (existing refactored db services)
```

## 3. Core Components and Logic

### 3.1. `scanner.py` - The Source Code Parser

-   **Responsibility:** To walk a given project directory and parse supported source files (e.g., Python files).
-   **Implementation:** It will use Python's built-in `ast` module to traverse the Abstract Syntax Tree of each file.
-   **Output:** It will extract structured information about:
    -   Folders and files.
    -   Class and function definitions, including their names and line numbers.
    -   Import statements (`import` and `from ... import`).
    -   Function calls within the code.

### 3.2. `factories.py` - Node and Edge Creation

-   **Responsibility:** To provide a centralized way to create valid `Node` and `Edge` model instances. This decouples the builder from the specific details of model creation.
-   **`NodeFactory` Class:**
    -   Methods like `create_folder_node(path)`, `create_file_node(path)`, `create_function_node(name, qname, position)`.
    -   Each method will correctly populate a `Node` object with the right `node_type` and `properties`.
-   **`EdgeFactory` Class:**
    -   Methods like `create_contains_edge(_from, _to, position)`, `create_call_edge(_from, _to, position)`.
    -   Each method will create the appropriate edge model (`ContainsEdge`, `CallEdge`, etc.).

### 3.3. `builder.py` - The Graph Orchestrator

-   **Responsibility:** To orchestrate the entire graph construction process. It will use the `scanner` to get code information, the `factories` to create graph objects, and the `db_service` to save them to ArangoDB.
-   **`GraphBuilder` Class:**
    -   A main method `build_graph_for_project(project_doc: Project)`.
    -   It will maintain a map of file paths and qualified names to their corresponding ArangoDB document `_id`s to avoid re-creating nodes and to easily link them.
    -   **Logic Implementation:**
        -   **Folders & Files:** Create `FOLDER` and `FILE` nodes. Link them with `ContainsEdge`.
        -   **File Contents:** For each file, create `FUNCTION`, `CLASS`, and `IMPORT` nodes. Link them to the file node with a `ContainsEdge`, including position data.
        -   **Calls:** Create `CallEdge` between functions/classes that call each other.
        -   **Imports:** Link `IMPORT` nodes to the functions/classes that use them.

### 3.4. `validator.py` - Graph Integrity

-   **Responsibility:** To run checks on the generated graph to ensure it is structurally sound.
-   **`GraphValidator` Class:**
    -   A main method `validate(project_key)`.
    -   **Checks to Implement:**
        -   **Orphaned Nodes:** Find any nodes (other than the project root) that do not have an incoming `ContainsEdge` or `BelongsToEdge`.
        -   **Invalid Edges:** Ensure that edges only connect valid node types (e.g., a `CallEdge` should originate from a `FUNCTION` or `CLASS`).
        -   **Missing Positions:** Ensure all `ContainsEdge`, `CallEdge`, and `ImportEdge` instances have valid position data.

## 4. Implementation Steps

1.  Create the `graph` directory and the empty files: `builder.py`, `factories.py`, `scanner.py`, `validator.py`.
2.  Implement `factories.py` with the `NodeFactory` and `EdgeFactory`.
3.  Implement a basic version of the `scanner.py` using `os.walk` and Python's `ast` module.
4.  Implement the `builder.py` to tie the scanner, factories, and database services together.
5.  Implement the `validator.py` with the initial set of validation rules.
6.  Create a new API endpoint (e.g., `POST /projects/{project_key}/scan`) to trigger the `GraphBuilder`.
7.  Update tests to cover the new graph building and validation logic.
