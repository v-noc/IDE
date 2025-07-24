# Symbol Table Design

This document details the design of the `SymbolTable`, the central component for resolving names, types, and dependencies during the parsing process.

## Core Concept: A Bridge to the Database

The `SymbolTable` is not a standalone data structure. It is a **stateful, in-memory cache and resolution engine** that sits in front of the ArangoDB database. Its primary purpose is to minimize database queries and to hold the contextual information needed to resolve symbols within a specific file or scope.

It will be initialized once by the `ProjectScanner` and passed through to all other components, acting as the single source of truth during the parsing operation.

## Data Structures

The `SymbolTable` will manage several internal dictionaries to track the state of the analysis:

1.  `_qname_to_id: dict[str, str]`: A cache that maps a symbol's fully qualified name (e.g., `my_project.utils.get_user`) to its database `_id` (e.g., `nodes/12345`). This is the most important cache for performance, as it prevents us from having to query the database for the same symbol repeatedly.
2.  `_file_id_to_imports: dict[str, dict[str, str]]`: A mapping of a file's `_id` to a dictionary of its imports. This inner dictionary maps an alias or imported name (e.g., `u`, `Request`) to the `qname` of the symbol it represents (e.g., `my_project.utils`, `fastapi.Request`).
3.  `_scope_variables: dict[str, str]`: A dictionary that tracks the type of variables within the current scope (e.g., a function). It maps the variable name (e.g., `my_user`) to the `_id` of its type's `Node` (e.g., the `_id` of the `User` class node).

## Leveraging ArangoDB and the ORM

The `SymbolTable` will interact with the database in a highly controlled manner:

-   **During the Declaration Pass:** When the `DeclarationVisitor` finds a new class or function, the `ProjectScanner` will create the corresponding `Node` model and save it to the database via the ORM. The `ProjectScanner` will then call `symbol_table.add_symbol(qname, db_id)` to populate the `_qname_to_id` cache.
-   **During the Detail Pass:** When the `DetailVisitor` needs to resolve a symbol, it will ask the `SymbolTable`. The `SymbolTable` will **not** perform complex graph traversals itself. Instead, it will use its caches and, if necessary, perform simple, targeted lookups using the existing ORM methods like `db.nodes.find({"qname": qname})`.

## The Resolution Process: A Detailed Example

This is the most critical logic. Let's trace how a call is resolved.

**Scenario:** The `DetailVisitor` is inside the `main` function in `main.py` and encounters the AST node for the call `u.get_user_name(user)`.

1.  **Visitor Request:** The visitor calls `symbol_table.resolve_call_target("u.get_user_name", current_file_id="files/main_py_id")`.
2.  **SymbolTable Logic:**

    a.  **Deconstruct the Name:** The table splits `u.get_user_name` into a base (`u`) and attributes (`get_user_name`).

    b.  **Check Local Scope:** It first checks `_scope_variables` to see if `u` is a local variable. Let's say it's not.

    c.  **Check File Imports:** It then looks up `current_file_id` in `_file_id_to_imports`. It finds that `u` is an alias for the `qname` `my_project.utils`.

    d.  **Construct Target QName:** It combines the resolved base with the attribute to get a target `qname`: `my_project.utils.get_user_name`.

    e.  **Check QName Cache:** It looks up this `qname` in its `_qname_to_id` cache. Because the declaration pass has already run for all files, the `utils.py` file and its `get_user_name` function have been processed, and their `_id`s are in the cache. It finds the corresponding database `_id` (e.g., `nodes/func_get_user_name_id`).

    f.  **Return ID:** The `SymbolTable` returns the resolved `_id`.
    
3.  **Edge Creation:** The `FileParser` now has the `_from` `_id` (the `main` function) and the `_to` `_id` (the `get_user_name` function). It can create the `CallEdge` Pydantic model and return it to the `ProjectScanner` to be saved.

## Handling External Packages

-   When an import is encountered that cannot be resolved to a local file (e.g., `import pydantic`), the `SymbolTable` will attempt to create a `qname` for it (e.g., `pydantic`).
-   The `ProjectScanner` will then create a `PackageNode` with this `qname` and add it to the `SymbolTable`'s cache. This allows us to link internal code to the external packages it uses.

## Schema Impact

This design works perfectly with the existing `node.py` and `edge.py` models. The `qname` field on the `Node` models is the key that makes this entire system work. No schema changes are required. The `SymbolTable` simply provides the logic to connect the nodes that the ORM manages.
