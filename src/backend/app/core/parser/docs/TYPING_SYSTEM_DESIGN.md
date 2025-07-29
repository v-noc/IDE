
# Typing System Design (Easy-to-Hard Approach)

## 1. High-Level Goals

The current typing system has limitations in representing complex types and linking them to corresponding class nodes. This document outlines a new design to address these issues, focusing on:

- **Readability:** The type information should be easy to understand and query.
- **Accuracy:** The system must accurately represent complex Python types, including generics (`List`, `Dict`, `Union`, `Optional`).
- **Queryability:** It should be easy to query for functions or classes based on their types (e.g., "find all functions that return a `User` object").
- **Extensibility:** The system should be designed to accommodate future enhancements.

## 2. Core Concept: From Strings to Structured Models

The fundamental shift in this design is to move from storing types as simple strings (e.g., `"Optional[User]"`) to structured Pydantic models that capture the full type information, including nested types and links to other nodes.

## 3. Phase 1: The Foundation (The "Easy" Part)

We start by building the data models and parsing the simplest types.

### Step 1.1: Define the New Data Models

First, we define the building blocks in `src/backend/app/models/properties.py`.

```python
# In src/backend/app/models/properties.py
from typing import Union, List, Optional
from pydantic import BaseModel, Field

# --- Type Representation Models ---

class BuiltinTypeReference(BaseModel):
    """Represents a built-in Python type (e.g., str, int)."""
    type_name: str

class CustomTypeReference(BaseModel):
    """Represents a custom type that links to a class node."""
    type_name: str
    linked_node_id: str

class GenericTypeReference(BaseModel):
    """Represents a generic type (e.g., List[User], Dict[str, int])."""
    type_name: str  # e.g., "List", "Dict", "Union", "Optional"
    parameters: List["TypeReference"]

# A Union to represent any possible type structure
TypeReference = Union[
    BuiltinTypeReference,
    CustomTypeReference,
    GenericTypeReference
]

# --- Updated Node Properties ---

class FunctionInput(BaseModel):
    name: str
    type_ref: TypeReference
    position: NodePosition

class FunctionOutput(BaseModel):
    type_ref: TypeReference
    position: NodePosition

class ClassField(BaseModel):
    name: str
    type_ref: TypeReference
    position: NodePosition

class FunctionProperties(BaseProperties):
    position: NodePosition
    inputs: List[FunctionInput] = Field(default_factory=list)
    outputs: List[FunctionOutput] = Field(default_factory=list)

class ClassProperties(BaseProperties):
    position: NodePosition
    fields: List[ClassField] = Field(default_factory=list)
```

### Step 1.2: Implement the Base Parser in `type_inference_visitor.py`

We create a new recursive function, `_parse_type_annotation`, to handle `ast.Name` nodes, which represent simple types like `str` or `User`.

```python
# In TypeInferenceVisitor class

def _parse_type_annotation(self, node: ast.AST) -> Optional[TypeReference]:
    if isinstance(node, ast.Name):
        type_name = node.id
        # Case 1: Built-in type (e.g., 'str', 'int')
        if type_name in self.builtin_types:
            return BuiltinTypeReference(type_name=type_name)
        
        # Case 2: Custom type (e.g., 'User')
        # We look up the symbol in the table, which was populated during import analysis.
        symbol_id = self.context.symbol_table.get_symbol_id(type_name)
        if symbol_id:
            return CustomTypeReference(type_name=type_name, linked_node_id=symbol_id)
            
    # Return None for unhandled types for now
    return None
```

At this stage, the system can correctly parse `-> str` and `-> User`, creating either a `BuiltinTypeReference` or a `CustomTypeReference` with a direct link to the `User` class node.

## 4. Phase 2: Handling Generics (The "Medium" Part)

Now we extend the parser to handle generic types like `List[User]` and `Optional[User]`.

### Step 2.1: Extend the Parser for `ast.Subscript`

We add logic to `_parse_type_annotation` to handle `ast.Subscript` nodes, which represent types with parameters (e.g., `List[...]`).

```python
# In _parse_type_annotation function

# ... (previous code for ast.Name)

    elif isinstance(node, ast.Subscript):
        # The outer type (e.g., 'List', 'Optional')
        outer_type_name = self._ast_to_string(node.value)
        
        # The inner type(s)
        slice_node = node.slice
        
        parameters = []
        # In Python 3.9+, slice is a single node. Older versions use ast.Index.
        # For simplicity, let's assume we can get a tuple of inner nodes.
        inner_nodes = []
        if isinstance(slice_node, ast.Tuple): # For Union[A, B], Dict[A, B]
            inner_nodes = slice_node.elts
        else: # For List[A], Optional[A]
            inner_nodes = [slice_node]

        for inner_node in inner_nodes:
            # *** RECURSIVE CALL ***
            # We recursively parse the inner types.
            param_ref = self._parse_type_annotation(inner_node)
            if param_ref:
                parameters.append(param_ref)
        
        if parameters:
            return GenericTypeReference(type_name=outer_type_name, parameters=parameters)

# ... (rest of the function)
```

### How it Grows:

-   **Parsing `List[User]`:**
    1.  The parser sees an `ast.Subscript`. `outer_type_name` becomes `"List"`.
    2.  It finds one inner node: `ast.Name(id='User')`.
    3.  It recursively calls `_parse_type_annotation` on the `User` node.
    4.  The inner call returns `CustomTypeReference(type_name='User', linked_node_id='...')`.
    5.  The outer call assembles the final model: `GenericTypeReference(type_name='List', parameters=[CustomTypeReference(...)])`.

-   **Parsing `Optional[User]`:**
    *   This works identically to `List[User]`, as `Optional[T]` is treated as a generic with one parameter. The result is `GenericTypeReference(type_name='Optional', parameters=[...])`.

## 5. Phase 3: Complex Nesting & Unions (The "Hard" Part)

The recursive nature of our parser means it can already handle deeply nested types without much extra logic.

### How it Grows:

-   **Parsing `Union[User, str]`:**
    1.  The parser sees an `ast.Subscript` with `outer_type_name` as `"Union"`.
    2.  The `slice` is an `ast.Tuple` containing two `ast.Name` nodes: `User` and `str`.
    3.  The parser loops through them, recursively calling `_parse_type_annotation` for each.
    4.  This results in two models: `CustomTypeReference(type_name='User', ...)` and `BuiltinTypeReference(type_name='str')`.
    5.  The final model is `GenericTypeReference(type_name='Union', parameters=[CustomTypeReference(...), BuiltinTypeReference(...)])`.

-   **Parsing `Optional[List[Union[User, str]]]`:**
    *   The beauty of the recursive design is that this works automatically.
    *   The call stack would look like:
        1.  `parse(Optional[...])` -> creates `GenericTypeReference(type_name='Optional', ...)`
        2.  `parse(List[...])` -> creates `GenericTypeReference(type_name='List', ...)`
        3.  `parse(Union[...])` -> creates `GenericTypeReference(type_name='Union', ...)`
        4.  `parse(User)` -> creates `CustomTypeReference`
        5.  `parse(str)` -> creates `BuiltinTypeReference`
    *   Each call returns its structured model to its parent, which embeds it in its `parameters` list, resulting in a perfectly nested Pydantic model that represents the entire complex type.

## 6. Integration with the Import System

This entire process is underpinned by the `DependencyVisitor` and `SymbolTable`.

-   **`UsesImportEdge`**: Tracks **file-to-file** dependencies. It's created first and ensures the `SymbolTable` knows where to find the definitions of imported types.
-   **`SymbolTable`**: Acts as a lookup map. When the `TypeInferenceVisitor` sees a name like `User`, it asks the `SymbolTable`, "What is the node ID for `User`?"
-   **`CustomTypeReference.linked_node_id`**: Stores the result of that lookup, creating the final, direct **type-to-node** link.
