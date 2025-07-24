# Symbol Table Persistence and Scope Tracking

This document details the advanced design for the `SymbolTable`, focusing on how it will manage, persist, and reconstruct scope information using the extended database schema.

## Core Principle: Scopes are Nodes

The fundamental change is that **scopes themselves are treated as nodes in the graph**. A function is a scope. A class is a scope. A file (for global scope) is a scope. This aligns perfectly with our node-based database model.

The `SymbolTable` will no longer hold a temporary, in-memory dictionary for scope variables. Instead, it will manage a **scope stack** where each item on the stack is the `_id` of a scope-defining node (like a `FunctionNode` or `FileNode`).

## The New Workflow

### During the Declaration Pass
1.  When the `DeclarationVisitor` finds a global variable assignment (`MY_VAR = "foo"`), the `FileParser` will create a `GlobalVariableNode` and a `DefinesEdge` linking the `FileNode` to the new `GlobalVariableNode`.
2.  This `GlobalVariableNode` is saved to the database and its `qname` and `_id` are cached in the `SymbolTable`.

### During the Detail Pass (`TypeInferenceVisitor`)
This is where the scope stack comes into play.

1.  **Entering a Scope:** When the `TypeInferenceVisitor`'s `visit_FunctionDef` method is called, it will:
    a.  Get the `_id` of the `FunctionNode` it's visiting.
    b.  **Push the `_id` onto the `SymbolTable`'s scope stack.**

2.  **Tracking Variables:** When the visitor's `visit_Assign` method finds a variable assignment (e.g., `my_user = User()`), it will:
    a.  Get the current scope `_id` by peeking at the top of the `SymbolTable`'s scope stack.
    b.  Resolve the type (`User`) to its `_id` as usual.
    c.  Create a `VariableNode` (a new, simpler node type for local variables) and a `DefinesEdge` linking the current scope's `_id` to the new `VariableNode`'s `_id`.
    d.  These new nodes and edges are added to the results list to be saved by the `ProjectScanner`.

3.  **Exiting a Scope:** When the `TypeInferenceVisitor` is done visiting the function, its `visit_FunctionDef` method will **pop the `_id` from the `SymbolTable`'s scope stack.**

### Resolving Calls (`CallVisitor`)
When the `CallVisitor` needs to resolve a call target, the `SymbolTable`'s `resolve_call_target_to_id` method will now have a much more powerful way to work:

1.  It receives the name to resolve (e.g., `my_user.get_name()`).
2.  It receives the current scope stack from the `SymbolTable`.
3.  It can now perform a query: "Starting from the current scope node, walk up the `DEFINES` edges to find a variable named `my_user`. Once found, get its `inferred_type_qname` and then find the `get_name` method on that type."

This is a graph traversal, but it can be implemented efficiently with targeted AQL queries that the `SymbolTable` can construct and execute via the ORM.

## Loading Scopes from the Database

With this design, the scope information is **fully persisted in the graph**. When the analysis is complete, the database contains a complete and queryable representation of every scope and the variables defined within it.

If we need to "reconstruct" the scope for a later analysis or query, we don't need to re-parse the file. We can simply run an AQL query to traverse the `DEFINES` edges starting from any given function or file node.

This approach is highly scalable, fully persistent, and turns our code analysis graph into a much more powerful and accurate representation of the codebase.
