# Proposed Improvements and Simplifications

This document proposes two major improvements to our design that will simplify the models, reduce the complexity of the visitors, and make the final graph more powerful and easier to query.

---

## Proposal 1: Flatten Node Properties

**Problem:** Our current node models (e.g., `FunctionNode`) contain a nested `properties` field (e.g., `FunctionProperties`). This adds a layer of complexity to both creating the models and querying them in ArangoDB. For example, to get the start line of a function, you need to access `function_node.properties.start_line`.

**Solution:** Merge the `properties` models directly into their parent `Node` models.

**Example (Before):**
```python
class FunctionProperties(BaseModel):
    start_line: int
    end_line: int

class FunctionNode(BaseNode):
    node_type: Literal["function"] = "function"
    qname: str
    properties: FunctionProperties
```

**Example (After):**
```python
class FunctionNode(BaseNode):
    node_type: Literal["function"] = "function"
    qname: str
    start_line: int
    end_line: int
```

**Benefits:**
-   **Simpler Models:** The Pydantic models become flatter and easier to read.
-   **Easier Queries:** AQL queries become simpler. You can write `RETURN doc.start_line` instead of `RETURN doc.properties.start_line`.
-   **Reduced Complexity:** The visitors no longer need to create two separate models (the node and its properties); they can create a single, flat node model.

---

## Proposal 2: Model Control Flow as an "Execution Graph"

**Problem:** The `CONTROL_FLOW_DESIGN.md` introduces many new node types (`IfNode`, `ForLoopNode`, etc.) and a complex `BRANCHES` edge to connect them. This logic can become very tangled, especially with nested conditions.

**Solution:** Instead of creating many new node types, we can represent control flow using a more standard **Control Flow Graph (CFG)** approach with just two new, highly specific edge types. We keep the `IfNode`, `ForLoopNode`, etc., but their connections become much cleaner.

**New Edges:**
-   **`EXECUTES`**: A simple, directed edge that shows the unconditional next step in execution.
-   **`HAS_CONDITION`**: An edge linking a control flow node (like `IfNode`) to the nodes that make up its condition.

**How it Works:**
-   A `FunctionNode` has one outgoing `EXECUTES` edge to the first statement or control block inside it.
-   Each statement has one `EXECUTES` edge to the next statement.
-   An `IfNode` has **two** outgoing `EXECUTES` edges:
    -   One labeled with `{"branch": "true"}` pointing to the first statement in its `body`.
    -   One labeled with `{"branch": "false"}` pointing to the first statement in its `orelse` block (or the statement after the `if` if there is no `else`).
-   A `ForLoopNode` has an `EXECUTES` edge to the first statement in its body, and the last statement in its body has an `EXECUTES` edge back to the `ForLoopNode`.

**Visual Example:**

Consider this code:
```python
def my_func(x):
    if x > 10:
        foo()
    else:
        bar()
    baz()
```

**The New Graph Structure:**
-   `FunctionNode(my_func)` -> `EXECUTES` -> `IfNode(x > 10)`
-   `IfNode(x > 10)` -> `EXECUTES {branch: true}` -> `CallNode(foo)`
-   `IfNode(x > 10)` -> `EXECUTES {branch: false}` -> `CallNode(bar)`
-   `CallNode(foo)` -> `EXECUTES` -> `CallNode(baz)`
-   `CallNode(bar)` -> `EXECUTES` -> `CallNode(baz)`

**Benefits:**
-   **True Control Flow Graph:** The graph now directly represents the flow of execution, which is incredibly powerful for analysis.
-   **Massively Simplified Visitor Logic:** The `ControlFlowVisitor` no longer needs to manage complex `BRANCHES` logic. It just needs to create the nodes and the simple, directed `EXECUTES` edges.
-   **Powerful Queries:** It becomes trivial to ask questions like:
    -   "Is it possible for `foo()` to be called and then `bar()` to be called in the same function run?" (No, because there is no path from `foo` to `bar`).
    -   "What is every possible execution path through this function?" (This is now a standard graph traversal problem).

These two proposals, especially the Execution Graph, would represent a significant improvement in the elegance and power of our final product, while also making the implementation process easier and less error-prone.
