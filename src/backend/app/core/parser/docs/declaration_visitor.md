# `DeclarationVisitor`

**Inherits from:** `ast.NodeVisitor`

**Purpose:** To perform the first, high-speed pass over a file's AST to identify all high-level symbol declarations.

## Class Design

```python
class DeclarationVisitor(ast.NodeVisitor):
    """
    A visitor that collects all function, class, and import declarations
    from a file's AST.
    """
    def __init__(self):
        self.declared_functions: list[ast.FunctionDef] = []
        self.declared_classes: list[ast.ClassDef] = []
        self.imports: list[ast.Import | ast.ImportFrom] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """
        Identifies a function definition.

        This method appends the raw AST node for the function to the
        `declared_functions` list. It does NOT visit the body of the function,
        ensuring the declaration pass remains fast.
        """
        self.declared_functions.append(node)
        # Note: No call to self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """
        Identifies a class definition.

        This method appends the raw AST node for the class to the
        `declared_classes` list. It then calls `generic_visit` to ensure
        that nested classes and methods are also declared.
        """
        self.declared_classes.append(node)
        self.generic_visit(node) # We need to find methods inside classes

    def visit_Import(self, node: ast.Import) -> None:
        """Identifies an `import ...` statement."""
        self.imports.append(node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Identifies a `from ... import ...` statement."""
        self.imports.append(node)
        self.generic_visit(node)
```

## Function-Level Documentation

### `__init__(self)`
-   **Description:** Initializes the visitor.
-   **Logic:** Creates empty lists to store the raw AST nodes that are discovered during the traversal. These lists are the primary output of this visitor.

### `visit_FunctionDef(self, node: ast.FunctionDef)`
-   **Description:** This method is called by the `ast.NodeVisitor` superclass for every function definition node in the AST.
-   **Logic:** It simply appends the `node` to the `self.declared_functions` list. It intentionally avoids calling `self.generic_visit(node)` for top-level functions to prevent the visitor from descending into the function's body, which is work reserved for the second pass.

### `visit_ClassDef(self, node: ast.ClassDef)`
-   **Description:** Called for every class definition.
-   **Logic:** It appends the `node` to `self.declared_classes`. Unlike `visit_FunctionDef`, it *does* call `self.generic_visit(node)`. This is a crucial distinction. We need to find the methods *declared* inside a class during the first pass so they can be correctly linked to the class.

### `visit_Import(self, node: ast.Import)` and `visit_ImportFrom(self, node: ast.ImportFrom)`
-   **Description:** Called for every import statement.
-   **Logic:** These methods append the raw import node to the `self.imports` list. This list will be used by the `PythonFileParser` to populate the `SymbolTable` with information about which modules are available in the file's scope.
