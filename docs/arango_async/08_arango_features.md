# ArangoDB Features & Query Tricks

## 1. Graph Traversal Tricks
ArangoDB's power lies in its graph capabilities. Here are tricks to master them.

### 1.1. `PRUNE` (The Performance Saver)
When traversing deep graphs (`1..100`), you often want to stop a path if a condition is met, but keep traversing others.
*   **Without PRUNE**: The traverser goes full depth, then `FILTER` removes results. (Wasteful)
*   **With PRUNE**: The traverser *stops* that branch immediately.

```aql
FOR v, e, p IN 1..100 OUTBOUND @start KEYWORDS(prune)
    // Stop going deeper if we hit a 'wrapper' node or a 'test' folder
    PRUNE v.node_type == "wrapper" OR v.name == "tests"
    RETURN v
```

### 1.2. `OPTIONS { uniqueVertices: 'global' }`
In your `get_containment_tree`, you might visit the same node via multiple paths (diamond dependency).
*   **global**: Ensures a vertex is visited *once* per query. Essential for DAGs.
*   **path**: Ensures uniqueness only within a single path (prevents cycles).

### 1.3. Edge Filters
You can filter edges *during* traversal, not just vertices.
```aql
FOR v, e IN 1..10 OUTBOUND 'nodes/1' edges
    FILTER e.type == "inheritance" // Only follow inheritance links
    RETURN v
```

## 2. AQL Power Features

### 2.1. Array Comparison Operators
Avoid loops in AQL. Use array operators.
*   `[*]` (Expansion): Extract a field from all items.
    ```aql
    // Get all IDs from a list of users
    RETURN users[*]._id
    ```
*   `ALL`, `ANY`, `NONE`:
    ```aql
    // Find documents where 'tags' array contains 'admin'
    FILTER 'admin' IN doc.tags
    
    // Find docs where ALL scores are > 10
    FILTER doc.scores ALL > 10
    ```

### 2.2. `COLLECT` (Aggregation)
Like SQL `GROUP BY`, but more flexible.
```aql
FOR doc IN calls
    COLLECT target = doc.target_id WITH COUNT INTO num_calls
    RETURN { target, num_calls }
```
**Tip**: `COLLECT ... INTO groups` keeps the original documents for each group.

### 2.3. `UPSERT` (Atomic Insert/Update)
You use this in `ensure_contains_edge`. It's atomic and race-condition free.
*   **Trick**: You can use it to increment counters atomically.
    ```aql
    UPSERT { _key: "visitor_count" }
    INSERT { _key: "visitor_count", val: 1 }
    UPDATE { val: OLD.val + 1 }
    IN counters
    ```

## 3. Async Specific Patterns

### 3.1. Fire-and-Forget (Background Tasks)
In a sync app, logging usage stats slows down the response. In async, you can create a background task.
```python
# In your API handler
async def handle_request():
    response = await db_work()
    # Schedule log writing without awaiting it
    asyncio.create_task(log_repo.write_access_log(user_id))
    return response
```

### 3.2. `asyncio.gather` for Parallel Graphs
If you need to fetch the "friends" of 10 users:
*   **Sequential**: 100ms * 10 = 1s
*   **Parallel**: 100ms (Total)

```python
users = await get_users()
tasks = [get_friends(u.id) for u in users]
all_friends = await asyncio.gather(*tasks)
```

## 4. Debugging Slow Queries

### 4.1. `PROFILE`
Prepend `PROFILE` to any AQL query in the ArangoDB Web UI.
It shows:
1.  **Execution Plan**: Are indexes used?
2.  **Profile**: Where was time spent? (traversal, filtering, calculating)

### 4.2. Index Utilization
If you see `Collection Scan` in the plan, you are missing an index.
*   **Persistent Index**: Good for equality (`email == "x"`) and range (`age > 18`).
*   **TTL Index**: Automatically delete old logs after X seconds. (Great for `CallNode` logs if they expire).

## 5. Summary of Tricks for your Migration
1.  **Refactor `NodeRepository.get_containment_tree`**: Use `batch_size` and stream results.
2.  **Use `TaskGroup`**: In `CallSyncService`, parallelize checking siblings.
3.  **Optimize `CallRepo`**: Ensure `targets_edges` has an index on `_to` if you often search backlinks.
