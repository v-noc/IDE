# `DependencyVisitor` Design

**Inherits from:** `ast.NodeVisitor`

**Purpose:** To resolve all `import` statements, determine if they refer to local project modules or external packages, and create the necessary `UsesImportEdge` models.

## Class Design
```python
class DependencyVisitor(ast.NodeVisitor):
    def __init__(self, context: VisitorContext):
        self.context = context
        self.current_consumer_id: str | None = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # ... implementation ...

    def visit_Name(self, node: ast.Name) -> None:
        # ... implementation ...

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # ... implementation ...
```

## Core Logic: Resolving Local vs. Package

The `SymbolTable` will contain the logic to differentiate between local modules and external packages.

1.  **Pre-computation:** During the **declaration pass**, the `ProjectScanner` will have already created `FileNode` objects for every `.py` file in the project. The `SymbolTable` will be populated with the `qname` of every one of these files (e.g., `my_project.utils`).
2.  **Resolution in `SymbolTable`:** The `SymbolTable` will have a method `resolve_import_qname(import_name: str)`.
    -   When the `DependencyVisitor` encounters an import like `import my_project.utils`, the `SymbolTable` will check if `my_project.utils` exists in its cache of known file `qname`s. If yes, it's a **local module**.
    -   If it encounters `import pydantic`, it will check its cache and not find a matching local file. It will therefore classify it as an **external package**. The `ProjectScanner` will then be responsible for creating a `PackageNode` for `pydantic` if one doesn't already exist.

## Function-Level Documentation

### `visit_FunctionDef(self, node: ast.FunctionDef)`
-   **Description:** Sets the context for which function is currently being analyzed. This is crucial for creating the `_from` part of the `UsesImportEdge`, as it tells us *who* is consuming the import.
-   **Logic:**
    1.  It gets the `qname` of the function from its `ast` node.
    2.  It uses the `SymbolTable` to look up the database `_id` for that `qname`.
    3.  It sets `self.current_consumer_id` to this `_id`.
    4.  It calls `self.generic_visit(node)` to traverse the function's body.
    5.  After the visit is complete, it resets `self.current_consumer_id` to `None`.

### `visit_Name(self, node: ast.Name)`
-   **Description:** This handles the usage of simple imported names, like `Request` in `from fastapi import Request`.
-   **Logic:**
    1.  It takes the name (`node.id`).
    2.  It asks the `SymbolTable`: "For the current file, is the name `Request` an imported symbol?"
    3.  The `SymbolTable` checks its import map for the file. If it finds that `Request` is mapped to the `qname` `fastapi.Request`, it returns the `_id` of the `fastapi.Request` symbol (which could be a `PackageNode` or a more specific node if we parsed stubs).
    4.  If a symbol `_id` is returned, the visitor creates a `UsesImportEdge` from `self.current_consumer_id` to the resolved symbol `_id`.

### `visit_Attribute(self, node: ast.Attribute)`
-   **Description:** This handles the usage of aliased imports, like `u.get_user_name` where `u` is an alias for `utils`.
-   **Logic:**
    1.  It reconstructs the full name being accessed (e.g., `u.get_user_name`).
    2.  It passes this full name to the `SymbolTable` for resolution, which will perform the logic described above (resolving `u` to the `utils` module, etc.).
    3.  If a symbol `_id` is returned, it creates the `UsesImportEdge`.
