# `ControlFlowVisitor` Design

**Inherits from:** `ast.NodeVisitor`

**Purpose:** To pre-process the AST of each function to make all control flow, including implicit `else` blocks, explicit. This visitor does not create any database models itself; its only job is to modify the AST in memory to make it easier for later visitors to parse.

## Class Design
```python
class ControlFlowVisitor(ast.NodeVisitor):
    def __init__(self, context: VisitorContext):
        self.context = context

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        node.body = self._transform_body_with_implicit_else(node.body)
        self.generic_visit(node)

    def _has_return(self, node: ast.AST) -> bool:
        # ... implementation ...

    def _transform_body_with_implicit_else(self, body: list[ast.stmt]) -> list[ast.stmt]:
        # ... implementation ...
```

## Function-Level Documentation

### `visit_FunctionDef(self, node: ast.FunctionDef)`
-   **Description:** This is the entry point for the visitor's logic. For each function it visits, it immediately calls the transformation helper on the function's body.
-   **Logic:**
    1.  It takes the list of statements in the function's body (`node.body`).
    2.  It passes this list to `_transform_body_with_implicit_else`.
    3.  It replaces `node.body` with the new, transformed list of statements.
    4.  It then calls `self.generic_visit(node)` to ensure it processes nested functions correctly.

### `_has_return(self, node: ast.AST)`
-   **Description:** A helper function to determine if a given node or any of its children contains a `return` statement.
-   **Logic:** It performs a mini-walk through the AST of the input `node`. If it finds an `ast.Return` node at any level, it immediately returns `True`. Otherwise, it returns `False`. This is crucial for the transformation logic.

### `_transform_body_with_implicit_else(self, body: list[ast.stmt])`
-   **Description:** This is the core of the visitor. It iterates through a list of statements and identifies `if` statements that have an "implicit else" (i.e., the `if` block always returns, and there is code after it that is not an `elif` or `else`).
-   **Logic:**
    1.  It iterates through the `body` list with an index `i`.
    2.  If `body[i]` is an `ast.If` statement and its `orelse` block is empty:
    3.  It calls `self._has_return(body[i])` to check if the `if` block is guaranteed to return.
    4.  If it does, and if there are statements after the `if` block (`i + 1 < len(body)`), then all subsequent statements (`body[i+1:]`) constitute the implicit `else` block.
    5.  It creates a new `ast.If` node where the `body` is the same, but the `orelse` attribute is now set to the list of subsequent statements.
    6.  The original `if` statement and all the statements that were moved into the `orelse` block are replaced in the list by this single new `ast.If` node.
    7.  The function returns the new, transformed list of statements.
