# Detail-Pass Visitors

This document provides the detailed design for the pipeline of visitors that execute during the second pass of the analysis. They are run in a specific order, and each one builds upon the work of the previous ones.

---

## `VisitorContext` Class

Before detailing the visitors, we must define the context object that will be passed to each of them.

```python
class VisitorContext:
    """
    A data class to hold and share state between visitors in the pipeline.
    """
    def __init__(self, file_id: str, ast: ast.Module, symbol_table: SymbolTable):
        self.file_id: str = file_id
        self.ast: ast.Module = ast
        self.symbol_table: SymbolTable = symbol_table
        self.results: list[BaseEdge] = [] # The final output of the pipeline
```

---

## 1. `ControlFlowVisitor`

**Inherits from:** `ast.NodeVisitor`

**Purpose:** To pre-process the AST to make control flow explicit.

### Class Design
```python
class ControlFlowVisitor(ast.NodeVisitor):
    def __init__(self, context: VisitorContext):
        self.context = context

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """
        Applies the implicit else transformation to the function body.
        """
        node.body = self._transform_body_with_implicit_else(node.body)
        self.generic_visit(node)

    def _transform_body_with_implicit_else(self, body: list[ast.stmt]) -> list[ast.stmt]:
        # ... implementation of the transformation logic ...
        return new_body
```

### Function-Level Documentation
-   `__init__(self, context)`: Stores the shared `VisitorContext`.
-   `visit_FunctionDef(self, node)`: The core of this visitor. Before it lets the traversal continue into the function's body, it replaces the function's `body` with a transformed version where implicit `else` blocks are made explicit.
-   `_transform_body_with_implicit_else(self, body)`: A helper function containing the complex logic for the AST transformation.

---

## 2. `DependencyVisitor`

**Inherits from:** `ast.NodeVisitor`

**Purpose:** To create `UsesImportEdge` models for all used imports.

### Class Design
```python
class DependencyVisitor(ast.NodeVisitor):
    def __init__(self, context: VisitorContext):
        self.context = context
        self.current_consumer_id: str | None = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Set current consumer and visit children
        qname = self.context.symbol_table.get_qname_for_ast_node(node)
        self.current_consumer_id = self.context.symbol_table.get_id_by_qname(qname)
        self.generic_visit(node)
        self.current_consumer_id = None # Unset after visiting

    def visit_Name(self, node: ast.Name) -> None:
        # If node.id is an imported symbol, create an edge
        resolved_import = self.context.symbol_table.resolve_import_usage(
            name=node.id, file_id=self.context.file_id
        )
        if resolved_import and self.current_consumer_id:
            edge = UsesImportEdge(
                _from=self.current_consumer_id,
                _to=resolved_import.provider_id,
                # ... other edge properties ...
            )
            self.context.results.append(edge)
```
### Function-Level Documentation
-   `visit_FunctionDef(self, node)`: Sets the context for which function is currently being analyzed. This is crucial for creating the `_from` part of the `UsesImportEdge`.
-   `visit_Name(self, node)`: This is where the main logic resides. For every name encountered in the code, it asks the `SymbolTable` if this name corresponds to an imported symbol. If it does, and we are inside a function, it creates the `UsesImportEdge` and adds it to the shared `context.results`.

---

## 3. `TypeInferenceVisitor`

**Inherits from:** `ast.NodeVisitor`

**Purpose:** To track variable assignments to infer types.

### Class Design
```python
class TypeInferenceVisitor(ast.NodeVisitor):
    def __init__(self, context: VisitorContext):
        self.context = context
        self.current_scope_id: str | None = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Set current scope and visit children
        qname = self.context.symbol_table.get_qname_for_ast_node(node)
        self.current_scope_id = self.context.symbol_table.get_id_by_qname(qname)
        self.generic_visit(node)
        self.current_scope_id = None

    def visit_Assign(self, node: ast.Assign) -> None:
        # Infer type from assignment
        # e.g., my_user = User()
        if isinstance(node.value, ast.Call) and self.current_scope_id:
            type_name = ast.unparse(node.value.func)
            type_id = self.context.symbol_table.resolve_type_to_id(type_name)
            if type_id:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variable_name = target.id
                        self.context.symbol_table.add_variable_type_to_scope(
                            scope_id=self.current_scope_id,
                            var_name=variable_name,
                            type_id=type_id
                        )
```
### Function-Level Documentation
-   `visit_FunctionDef(self, node)`: Sets the current scope to the ID of the function being visited.
-   `visit_Assign(self, node)`: The core logic. It checks for assignments where the value is a class instantiation (an `ast.Call`). It resolves the type of the class being instantiated via the `SymbolTable` and then tells the `SymbolTable` to associate the variable name with the resolved type ID within the current scope.

---

## 4. `CallVisitor`

**Inherits from:** `ast.NodeVisitor`

**Purpose:** To resolve all function and method calls and create `CallEdge` models.

### Class Design
```python
class CallVisitor(ast.NodeVisitor):
    def __init__(self, context: VisitorContext):
        self.context = context
        self.current_caller_id: str | None = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        qname = self.context.symbol_table.get_qname_for_ast_node(node)
        self.current_caller_id = self.context.symbol_table.get_id_by_qname(qname)
        self.generic_visit(node)
        self.current_caller_id = None

    def visit_Call(self, node: ast.Call) -> None:
        # Resolve the call target and create an edge
        target_id = self.context.symbol_table.resolve_call_target_to_id(
            call_node=node,
            scope_id=self.current_caller_id
        )
        if target_id and self.current_caller_id:
            edge = CallEdge(
                _from=self.current_caller_id,
                _to=target_id,
                # ... other properties ...
            )
            self.context.results.append(edge)
```
### Function-Level Documentation
-   `visit_FunctionDef(self, node)`: Sets the context of the calling function.
-   `visit_Call(self, node)`: The final step. It takes the `ast.Call` node and passes it to the `SymbolTable`'s `resolve_call_target_to_id` method. This method will perform the complex resolution logic, leveraging the import and type inference data gathered by the previous visitors. If a target ID is found, it creates the `CallEdge` and adds it to the final results.
