# `TypeInferenceVisitor` Design

**Inherits from:** `ast.NodeVisitor`

**Purpose:** To track variable assignments within scopes to provide type information that the `CallVisitor` can use to resolve method calls.

## Class Design
```python
class TypeInferenceVisitor(ast.NodeVisitor):
    def __init__(self, context: VisitorContext):
        self.context = context

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # ... implementation ...

    def visit_Assign(self, node: ast.Assign) -> None:
        # ... implementation ...
```

## Function-Level Documentation

### `visit_FunctionDef(self, node: ast.FunctionDef)`
-   **Description:** Manages the scope stack in the `SymbolTable`.
-   **Logic:**
    1.  Gets the `_id` of the `FunctionNode` being visited.
    2.  Calls `self.context.symbol_table.push_scope(function_id)`.
    3.  Calls `self.generic_visit(node)` to traverse the function's body.
    4.  Calls `self.context.symbol_table.pop_scope()`. This is a critical step to ensure that when the visitor leaves the function, the scope is correctly removed from the stack.

### `visit_Assign(self, node: ast.Assign)`
-   **Description:** This is the core of the visitor. It identifies assignments and attempts to infer the type of the variable being assigned.
-   **Logic:**
    1.  It checks if the assignment is of the form `variable = SomeClass()`. This is identified when `node.value` is an `ast.Call`.
    2.  If it is, it gets the name of the class being instantiated (e.g., `User` from `User()`).
    3.  It asks the `SymbolTable` to resolve this type name to a `_id`. The `SymbolTable` will look in the file's imports and local declarations to find the `_id` of the `ClassNode` for `User`.
    4.  If the type is successfully resolved to an `_id`, the visitor gets the variable name being assigned to (e.g., `my_user`).
    5.  It then calls `self.context.symbol_table.add_variable_type_to_current_scope(variable_name, type_id)`. The `SymbolTable` will handle creating the `VariableNode` and `DefinesEdge` and adding them to the database.

---

# `CallVisitor` Design

**Inherits from:** `ast.NodeVisitor`

**Purpose:** To identify all function and method calls and create `CallEdge` models by resolving them to their definitions.

## Class Design
```python
class CallVisitor(ast.NodeVisitor):
    def __init__(self, context: VisitorContext):
        self.context = context
        self.current_caller_id: str | None = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # ... implementation ...

    def visit_Call(self, node: ast.Call) -> None:
        # ... implementation ...
```

## Function-Level Documentation

### `visit_FunctionDef(self, node: ast.FunctionDef)`
-   **Description:** Sets the context of which function is making the calls.
-   **Logic:**
    1.  Gets the `_id` of the `FunctionNode` being visited.
    2.  Sets `self.current_caller_id` to this `_id`.
    3.  Calls `self.generic_visit(node)`.
    4.  Resets `self.current_caller_id` to `None` after the visit.

### `visit_Call(self, node: ast.Call)`
-   **Description:** The final and most important step in the analysis. It resolves a call to its specific definition.
-   **Logic:**
    1.  It passes the `ast.Call` node to the `SymbolTable`'s `resolve_call_target_to_id` method.
    2.  The `SymbolTable` will perform the complex resolution:
        -   If the call is a simple function call like `get_user()`, it will look for an imported or locally defined function.
        -   If the call is a method call like `my_user.get_name()`, it will first resolve the type of `my_user` using its scope information (which the `TypeInferenceVisitor` provided). It will find that `my_user` is of type `User`. It will then look for a method named `get_name` on the `User` class.
    3.  If the `SymbolTable` successfully returns a target `_id`, the `CallVisitor` creates a `CallEdge` model with `_from` as `self.current_caller_id` and `_to` as the resolved target `_id`.
    4.  This new edge is appended to the shared `context.results` list.
