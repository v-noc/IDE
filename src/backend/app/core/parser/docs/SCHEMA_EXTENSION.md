# Schema Extension for Scopes and Variables

To properly track scopes and variables in a persistent way, we need to extend our database schema. This involves adding a new node type for variables and a new edge type to represent scope containment.

## 1. New Node Type: `GlobalVariableNode`

We will add a new node to our `app/models/node.py` discriminated union to represent global variables.

### `GlobalVariableNode`
-   **`node_type`**: `"global_variable"`
-   **`name`**: The name of the variable (e.g., `MY_CONSTANT`).
-   **`qname`**: The fully qualified name (e.g., `my_project.settings.MY_CONSTANT`).
-   **`properties`**: A new `GlobalVariableProperties` model.
    -   `inferred_type_qname`: A string representing the qualified name of the variable's inferred type (e.g., `builtins.str`). This is crucial for later analysis.

This allows us to treat global variables just like functions and classes—as distinct nodes in our graph.

## 2. New Edge Type: `DEFINES`

We need a way to link a scope (like a function or a class) to the variables that are defined within it. We will create a new edge for this.

### `DefinesEdge`
-   **`edge_type`**: `"defines"`
-   **`_from`**: The `_id` of the scope node (e.g., a `FunctionNode` or `ClassNode`).
-   **`_to`**: The `_id` of the `GlobalVariableNode` that is defined within that scope.
-   **`properties`**:
    -   `variable_name`: The simple name of the variable as it's used in the code (e.g., `my_user`).

## How This Changes the Graph

Previously, we only had `CONTAINS` edges linking files to functions/classes. Now, the hierarchy will be more detailed:

-   A `FileNode` will `CONTAINS` a `FunctionNode`.
-   That `FunctionNode` will `DEFINES` a `VariableNode` (representing a local variable).
-   A `FileNode` will `CONTAINS` a `GlobalVariableNode`.

This richer structure allows us to write powerful AQL queries to, for example, "find all variables of type 'User' defined anywhere in the project" or "show me all variables defined within the `get_user` function."

## Impact on Existing Models

-   **`app/models/node.py`**: Add `GlobalVariableNode` to the `Node` union.
-   **`app/models/properties.py`**: Add the `GlobalVariableProperties` model.
-   **`app/models/edges.py`**: Add the `DefinesEdge` model.

This extension provides the necessary foundation to make scope and variable information a persistent and queryable part of our code graph.
