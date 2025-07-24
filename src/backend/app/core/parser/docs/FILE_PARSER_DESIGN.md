# FileParser Design

This document details the design of the `PythonFileParser` class. This class orchestrates the two-pass parsing process for a single Python file.

## Responsibilities

The `PythonFileParser` is the engine that drives the analysis of one file. It does not have complex logic itself; instead, it coordinates the `visitors` and the `SymbolTable` to produce the final Pydantic models.

1.  **Orchestration:** It manages the two-pass analysis for a single file.
2.  **Data Transformation:** It takes the raw `ast` nodes from the visitors and uses the `SymbolTable` to transform them into structured Pydantic `Node` and `Edge` models.
3.  **Isolation:** It provides a clean separation between the project-level orchestration (`ProjectScanner`) and the low-level AST traversal (`visitors`).

## Workflow

The `ProjectScanner` will use this class as follows:

### First Pass: `run_declaration_pass()`

1.  **Input:** Takes the file's path and content.
2.  **AST Parsing:** Parses the file content into an `ast.Module` object and caches it in the `ASTCache`.
3.  **Visitor Execution:** Instantiates and runs the `DeclarationVisitor` on the AST.
4.  **Node Creation:**
    *   It gets the lists of raw `ast` nodes (functions, classes, imports) from the visitor.
    *   It iterates through them, creating a `qname` for each one (e.g., `my_project.my_module.MyClass`).
    *   It instantiates the corresponding Pydantic `Node` models (`FunctionNode`, `ClassNode`).
    *   It also processes the imports and calls `symbol_table.add_import()` for each one.
5.  **Output:** Returns a list of Pydantic `Node` objects to the `ProjectScanner`.

### Second Pass: `run_detail_pass()`

1.  **Input:** Takes the file's path.
2.  **AST Retrieval:** Retrieves the cached AST from the `ASTCache`.
3.  **AST Transformation:** Pre-processes the function bodies in the AST using the `transform_body_with_implicit_else` utility.
4.  **Visitor Execution:** Instantiates and runs the `DetailVisitor` on the transformed AST.
5.  **Edge Creation:**
    *   It gets the lists of raw `ast` nodes representing calls and other details from the visitor.
    *   It iterates through each raw call.
    *   For each call, it asks the `SymbolTable` to resolve the target function/method and get its `_id`.
    *   It then creates the `CallEdge` Pydantic model, linking the `_id` of the calling function to the `_id` of the target function.
    *   It performs a similar process for creating `UsesImportEdge` and other edges.
6.  **Output:** Returns a list of Pydantic `Edge` objects to the `ProjectScanner`.

## Non-Responsibilities

-   The `FileParser` **does not** save anything to the database. It only creates the Pydantic models. The `ProjectScanner` is responsible for the database interaction.
-   It **does not** discover files.
-   It **does not** manage the `SymbolTable`'s state beyond a single file.

This design makes the `FileParser` a stateless and highly focused component. Its job is to execute the parsing recipe for a single file and return the results, making it easy to test and reason about.
