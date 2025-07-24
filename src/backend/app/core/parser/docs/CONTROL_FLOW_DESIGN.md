# Control Flow Analysis Design

This document details the plan to extend the parser to analyze and model control flow structures (`if`, `match`, `for`, `while`). This involves extending the database schema and creating a dedicated visitor to handle the logic.

## Core Principle: Control Flow as Nodes

The fundamental design choice is to represent control flow blocks as distinct nodes in the graph. This allows us to attach detailed properties to them (like the conditions of an `if` statement) and to link them to the code that executes within them.

## 1. Schema Extensions

We will extend the models in `app/models/` to support these new structures.

### New Node Types

The `Node` discriminated union in `node.py` will be extended with:

-   **`IfNode`**: Represents an `if` or `elif` block.
    -   `properties`:
        -   `condition_str`: `str` - The string representation of the condition (e.g., `user.is_active()`).
        -   `condition_expr`: `dict` - A structured representation of the condition. For `x > 5`, this would be `{ "left": "x", "op": "Gt", "right": "5" }`. For complex conditions, this can be a nested dictionary.
-   **`ElseNode`**: Represents an `else` block. It has no specific properties.
-   **`ForLoopNode`**: Represents a `for` loop.
    -   `properties`:
        -   `target_str`: `str` - The loop variable (e.g., `user`).
        -   `iterable_str`: `str` - The expression being iterated over (e.g., `active_users`).
-   **`WhileLoopNode`**: Represents a `while` loop. Its properties are identical to `IfNode`.
-   **`MatchNode`**: Represents a `match` statement.
    -   `properties`:
        -   `subject_str`: `str` - The variable or value being matched.
-   **`CaseNode`**: Represents a `case` block within a `match`.
    -   `properties`:
        -   `pattern_str`: `str` - The string representation of the case pattern.

### New Edge Types

The `edges.py` model will be extended with:

-   **`BRANCHES`**: This edge links control flow nodes together sequentially.
    -   `_from`: `FunctionNode` -> `_to`: First `IfNode` or `ForLoopNode` in the function.
    -   `_from`: `IfNode` -> `_to`: The next `IfNode` (`elif`) or `ElseNode`.
    -   `_from`: `IfNode` -> `_to`: The first `CallNode` or other statement inside its body.
    -   `_from`: `ForLoopNode` -> `_to`: The first statement inside its body.
-   **`CONDITION_OF`**: This is a critical new edge for linking conditions directly to function calls.
    -   `_from`: `IfNode` or `WhileLoopNode` -> `_to`: A `FunctionNode` that is called *within* the condition expression.
    -   **Example:** For `if user.is_active():`, this edge would link the `IfNode` for the `if` statement directly to the `FunctionNode` for `is_active`.

## 2. The `ControlFlowVisitor`

A new, dedicated visitor will be added to the second-pass pipeline. It will run **before** the `CallVisitor` but after the `TypeInferenceVisitor`.

**Inherits from:** `ast.NodeVisitor`

**Purpose:** To identify all control flow statements, create the corresponding `Node` and `Edge` models, and add them to the `VisitorContext` results.

### `visit_If(self, node: ast.If)`
-   **Logic:** This is the most complex method.
    1.  **Create `IfNode`:** It creates an `IfNode` for the current `if` block.
    2.  **Parse Condition:** It will parse `node.test`.
        -   It will generate the `condition_str` using `ast.unparse`.
        -   It will recursively parse the expression to create the `condition_expr` dictionary.
        -   **If `node.test` is an `ast.Call`:** It will use the `SymbolTable` to resolve the call target. If successful, it will create a `CONDITION_OF` edge linking the new `IfNode` to the resolved `FunctionNode`.
    3.  **Link to Body:** It will create `BRANCHES` edges from the `IfNode` to the statements inside `node.body`.
    4.  **Handle `orelse`:** It will recursively call itself on the `node.orelse` block. If the `orelse` is another `ast.If`, it creates another `IfNode` (for an `elif`). If it's a simple block, it creates an `ElseNode`. It then creates a `BRANCHES` edge from the current `IfNode` to the `elif`/`else` node.

### `visit_For(self, node: ast.For)`
-   **Logic:**
    1.  Creates a `ForLoopNode`.
    2.  Parses `node.target` and `node.iter` to populate the node's properties.
    3.  If `node.iter` is a function call, it resolves it and creates a `CONDITION_OF` edge (semantically, it's a call that *governs* the loop).
    4.  Creates `BRANCHES` edges to the statements inside `node.body`.

### `visit_While(self, node: ast.While)`
-   **Logic:** Very similar to `visit_If`. It creates a `WhileLoopNode` and parses the `node.test` condition, creating a `CONDITION_OF` edge if the condition is a direct function call.

## 3. Impact on Architecture

-   The `PARSER_ARCHITECTURE.md` needs to be updated to include the `ControlFlowVisitor` in the second-pass pipeline. It should run after type inference but before the main `CallVisitor`.
-   The `CallVisitor`'s job becomes simpler. It still finds all calls, but the `ControlFlowVisitor` has already created the graph structure that gives those calls context.

This design provides a much richer, more queryable graph. We can now ask questions like: "Show me all function calls that only happen if `user.is_admin` is true" or "Find all loops that iterate over the result of the `get_all_users` function."
