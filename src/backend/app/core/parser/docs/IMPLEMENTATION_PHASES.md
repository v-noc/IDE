# Phased Implementation and Testing Plan

This document breaks down the implementation of the code parser into a series of distinct, testable phases. Each phase builds upon the last, ensuring we have a solid foundation at every step.

---

## Phase 1: The Skeleton and Basic Declarations

**Goal:** To be able to parse a project and correctly identify all files, classes, and functions, creating their corresponding nodes in the database.

**Implementation Steps:**
1.  **Create the File Structure:** Create all the empty files and class skeletons as detailed in the design documents (`ast_cache.py`, `symbol_table.py`, `file_parser.py`, `declaration_visitor.py`, etc.).
2.  **Implement `FileNavigator`:** (Already exists, no action needed).
3.  **Implement `DeclarationVisitor`:** Implement the logic in `visit_FunctionDef` and `visit_ClassDef` to collect the raw AST nodes.
4.  **Implement `PythonFileParser.run_declaration_pass()`:** Implement the logic to run the `DeclarationVisitor` and transform its raw output into Pydantic `FunctionNode` and `ClassNode` models.
5.  **Implement `ProjectScanner` (First Pass only):** Implement the first loop of the `scan()` method. It should use the `FileParser` to get the list of declared nodes and then use the existing ORM to save them to the database.

**Testing Plan for Phase 1:**
-   **Unit Test:** Create a test file for `DeclarationVisitor` that feeds it a simple AST and asserts that `visitor.declared_functions` and `visitor.declared_classes` are populated correctly.
-   **Integration Test:** Create a test for `ProjectScanner` that points it at a small, sample project on disk (e.g., the `sample_project` in `tests/unit/core/parser/`). After running the first pass, query the database directly and assert that the correct `FunctionNode` and `ClassNode` objects have been created with the correct names and `qname`s.

---

## Phase 2: Dependency and Import Resolution

**Goal:** To correctly identify all imports, differentiate between local modules and external packages, and create `PackageNode`s and `UsesImportEdge`s.

**Implementation Steps:**
1.  **Implement `DependencyVisitor`:** Implement the `visit_Import`, `visit_ImportFrom`, `visit_Name`, and `visit_Attribute` methods.
2.  **Enhance `SymbolTable`:** Implement the `add_import` and `resolve_import_qname` logic. This is where you'll differentiate between local files (already in the symbol table from Phase 1) and external packages.
3.  **Enhance `PythonFileParser.run_detail_pass()`:** Add the `DependencyVisitor` to the pipeline.
4.  **Enhance `ProjectScanner` (Second Pass):** Implement the second loop to run the detail pass and save the resulting `UsesImportEdge` models.

**Testing Plan for Phase 2:**
-   **Unit Test:** Test the `SymbolTable`'s `resolve_import_qname` method directly. Give it a known set of file `qname`s and test its ability to correctly identify local vs. external imports.
-   **Integration Test:** Use the same sample project. After running the full scan, query the database for `PackageNode`s and `UsesImportEdge`s. Assert that:
    -   A `PackageNode` for `pydantic` (or another external library) exists.
    -   A `UsesImportEdge` correctly links a function that uses an import to the corresponding `FileNode` (for local imports) or `PackageNode` (for external imports).

---

## Phase 3: Control Flow Graph Construction

**Goal:** To build the full "Execution Graph" for each function, creating `IfNode`, `ForLoopNode`, `CallNode`, etc., and linking them with `EXECUTES` edges.

**Implementation Steps:**
1.  **Implement `ControlFlowVisitor`:** This is the most complex step. Implement the logic for visiting `If`, `For`, `While`, and `Call` nodes. This visitor will be responsible for creating both the control flow nodes and the `EXECUTES` edges that link them.
2.  **Implement `_transform_body_with_implicit_else`:** Create and test this crucial helper function.
3.  **Update `PythonFileParser.run_detail_pass()`:** Add the `ControlFlowVisitor` to the pipeline.

**Testing Plan for Phase 3:**
-   **Unit Test:** Create a dedicated test file for the `_transform_body_with_implicit_else` helper. Feed it various AST structures and assert that the output is transformed correctly.
-   **Integration Test:** Create a new, more complex sample project file that includes nested `if`/`else` blocks and loops. After running the scan, perform a graph traversal query (AQL) on the database to walk the `EXECUTES` edges from a function's entry point. Assert that the path of nodes returned by the query matches the expected execution flow of the code.

---

## Phase 4: Type Inference and Call Resolution

**Goal:** To resolve method calls (`my_var.do_thing()`) by tracking variable types within scopes.

**Implementation Steps:**
1.  **Implement `TypeInferenceVisitor`:** Implement the logic to track assignments and populate the `SymbolTable` with variable type information.
2.  **Enhance `SymbolTable`:** Implement the scope stack (`push_scope`, `pop_scope`) and the logic to associate variable names with type IDs within a given scope. Most importantly, implement the final `resolve_call_target_to_id` method.
3.  **Update `PythonFileParser.run_detail_pass()`:** Add the `TypeInferenceVisitor` to the pipeline *before* the `ControlFlowVisitor`.
4.  **Enhance `ControlFlowVisitor`:** The `visit_Call` method should now use the `SymbolTable` to resolve the call and create the final `CallEdge`.

**Testing Plan for Phase 4:**
-   **Integration Test:** Create a sample project with multiple files where one class (`User`) is defined in one file and instantiated and used in another. After scanning, assert that:
    -   A `CallEdge` correctly links the call `my_user.get_name()` to the `FunctionNode` for the `get_name` method defined inside the `User` class.
    -   This test is the ultimate validation of the entire system working together.

---

## Phase 5: Error Handling and Reporting

**Goal:** To make the parser resilient and provide useful feedback.

**Implementation Steps:**
1.  **Create `AnalysisReport` models.**
2.  Add `try...except` blocks to the `PythonFileParser` (for `SyntaxError`) and `ProjectScanner` (for internal errors).
3.  Modify the `SymbolTable` and visitors to log warnings to the report for unresolved symbols instead of crashing.
4.  Update the API endpoint to return the `AnalysisReport`.

**Testing Plan for Phase 5:**
-   **Integration Test:**
    -   Create a sample project file with a deliberate syntax error. Run the scan and assert that the returned `AnalysisReport` contains the correct `SyntaxError` issue and that the status is `completed_with_issues`.
    -   Create a file with an unresolvable import. Assert that the report contains the correct `UnresolvedImport` warning.
