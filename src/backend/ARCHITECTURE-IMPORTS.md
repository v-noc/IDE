# Refined Architecture for Handling Imports

This document outlines a new, improved architecture for representing import statements within the code graph. The current model, which uses both an `ImportNode` and an `ImportEdge`, is unnecessarily complex and lacks detail.

The new architecture is based on a single, powerful principle: **An import is an edge, not a node.**

## 1. Core Concepts

1.  **Imports as Edges:** An import will be represented by a single `UsesImportEdge`. This edge directly connects the code that *uses* an import (the consumer) to the code that is being imported (the provider).
2.  **Rich Edge Data:** The `UsesImportEdge` will be a rich object containing all relevant context: the alias (`as np`), the module path (`from ..utils`), the position of the import statement, and a list of positions where the import is actively used.
3.  **External Packages as Nodes:** To distinguish between internal code and external libraries, a new `PackageNode` will be introduced. This allows the graph to clearly represent dependencies on libraries like `fastapi` or `pydantic`.

## 2. Visualized Architecture

This new model simplifies the graph significantly:

*   **Internal Import:**
    `[Function: process_data]` -> `[UsesImportEdge]` -> `[Function: calculate_metrics]`

*   **External Import:**
    `[Function: create_app]` -> `[UsesImportEdge]` -> `[PackageNode: fastapi]`

## 3. Proposed Component & Model Changes

### 3.1. New Node Type: `PackageNode`

A new node to represent an external dependency.

*   **`models/node.py`:**
    ```python
    class PackageNode(BaseNode):
        node_type: str = "package"
        name: str  # e.g., "fastapi"
        qname: str # e.g., "fastapi"
        properties: PackageProperties
    ```
*   **`models/properties.py`:**
    ```python
    class PackageProperties(BaseProperties):
        version: str | None = None # e.g., "0.104.1"
        source: str | None = None  # e.g., "pypi"
    ```

### 3.2. New Edge Type: `UsesImportEdge`

This will replace the old `ImportEdge`. It's a highly descriptive edge.

*   **`models/edges.py`:**
    ```python
    class UsesImportEdge(BaseEdge):
        edge_type: str = "uses_import"
        
        # The code being imported (e.g., "my_function" from "my_module.my_function")
        target_symbol: str 
        
        # The alias, if one is used (e.g., "np" in "import numpy as np")
        alias: str | None = None
        
        # The position of the 'import ...' statement in the file
        import_position: NodePosition
        
        # A list of all positions where the imported code is used
        usage_positions: list[NodePosition] = Field(default_factory=list)
    ```

### 3.3. Model Deprecation

*   `ImportNode` will be **removed** from `models/node.py`.
*   `ImportProperties` will be **removed** from `models/properties.py`.
*   The old `ImportEdge` will be **removed** and replaced by `UsesImportEdge`.

## 4. Domain API Changes

### 4.1. New `Package` Domain Object

*   A new `core/package.py` file will be created for the `Package(DomainObject[node.PackageNode])` class.

### 4.2. `CodeGraphManager` Updates

*   The manager in `core/manager.py` will get a new method to handle packages:
    ```python
    def get_or_create_package(self, name: str, version: str | None = None) -> Package:
        # Finds or creates a PackageNode and returns the domain object.
    ```

### 4.3. `Function` and `Class` Updates

*   The `Function` and `Class` domain objects in `core/code_elements.py` will get a new method:
    ```python
    def uses_import(
        self,
        target: "Function" | "Class" | "Package",
        target_symbol: str,
        import_position: NodePosition,
        usage_positions: list[NodePosition],
        alias: str | None = None
    ) -> None:
        # Creates a UsesImportEdge from self to the target.
    ```

### 4.4. Domain Logic Deprecation

*   The `Import` domain object will be **removed** from `core/code_elements.py`.
*   The `add_import` method will be **removed** from `core/file.py`.

## 5. Refactoring and Implementation Steps

1.  **Approve Plan:** Confirm this architectural plan.
2.  **Refactor Models:**
    *   Update `models/properties.py` (add `PackageProperties`, remove `ImportProperties`).
    *   Update `models/node.py` (add `PackageNode`, remove `ImportNode`).
    *   Update `models/edges.py` (replace `ImportEdge` with `UsesImportEdge`).
3.  **Update DB Collections:** Modify `db/collections.py` to use the new `UsesImportEdge`.
4.  **Implement Domain Layer:**
    *   Create `core/package.py`.
    *   Update `core/manager.py` with package handling.
    *   Update `core/code_elements.py` with the `uses_import` method and remove the `Import` class.
    *   Remove the `add_import` method from `core/file.py`.
5.  **Update Services:** The `GraphBuilder` and `GraphScanner` services will need to be updated to use this new, more expressive import handling system.
6.  **Update Tests:** Adapt all relevant tests to the new architecture.
