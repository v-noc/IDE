# ArangoDB Query Analysis & Optimization

## 1. Overview
This document analyzes the critical AQL queries in the `v-noc` codebase, identifying performance bottlenecks and proposing optimization strategies using the new async driver. The primary focus is on large graph traversals and high-frequency lookups.

## 2. High-Impact Queries

### 2.1. The Bottleneck: `get_containment_tree`
**Location**: `src/backend/app/core/repository/base/node_repo.py`

#### Current Status
- **Purpose**: Fetches the entire hierarchy of a node (up to depth 50/100).
- **Complexity**: $O(V + E)$ where $V$ is vertices in the subtree.
- **Issue**: It builds a massive list in memory (`list(cursor)`) before returning. If a project has 10,000 files, this blocks the thread for seconds.
- **Sync Code**:
  ```python
  cursor = self.db.aql.execute(query, bind_vars=bind_vars)
  results = list(cursor)  # <-- MEMORY SPIKE & BLOCKING
  ```

#### Async Optimization Strategy
1.  **Stream, Don't Buffer**: Use `async for` to process nodes as they arrive from the DB.
2.  **Projection**: Ensure the AQL returns *only* needed fields. The current query returns `v` (whole document). If you only need ID and type for structure, select only those.
3.  **Async Implementation**:
    ```python
    async def get_containment_tree(self, start_node_id: str, ...) -> AsyncGenerator[Dict, None]:
        cursor = await self.db.aql.execute(query, ...)
        async for result in cursor:
            yield result
            # Or process in small batches
    ```

### 2.2. Recursive Call Counting: `count_recursive_calls_upward`
**Location**: `src/backend/app/core/repository/code_elements/call_repo.py`

#### Current Status
- **Purpose**: Detect recursion by walking up the call stack.
- **Issue**: Called frequently during graph building. Each call triggers a DB roundtrip.
- **Query**:
  ```aql
  FOR v IN 0..@max_depth INBOUND @start_parent_id @@contains
      PRUNE v.node_type != "call"
      ...
  ```

#### Async Optimization Strategy
1.  **Batching**: The `count_recursive_calls_upward_batch` method already exists. Ensure it is used!
2.  **Async Gather**: If you have 50 call sites to check, do not loop.
    ```python
    # Bad (Sequential Async)
    for call in calls:
        await repo.count_recursive_calls_upward(call)

    # Good (Concurrent)
    await asyncio.gather(*[repo.count_recursive_calls_upward(call) for call in calls])
    ```
3.  **PREFETCH Cache**: If traversing a known scope, fetch the entire call hierarchy once into a `NetworkX` graph in memory and query that, instead of hitting ArangoDB 50 times.

### 2.3. Edge Creation: `ensure_contains_edge`
**Location**: `src/backend/app/core/parser/graph_builder/sync/sync_helpers.py`

#### Current Status
- **Purpose**: Links nodes.
- **Issue**: 1 query per edge. "Death by a thousand cuts".
- **Query**: `UPSERT ... INSERT ... UPDATE`

#### Async Optimization Strategy
1.  **Bulk Import API**: For initial graph build, do not use AQL `UPSERT`. Use `import_bulk` API provided by `python-arango` (and likely available in async). It's 10x-50x faster.
2.  **Fire and Forget**: Edge creation often doesn't return data needed immediately. You can spawn these tasks and await them in a group later.

## 3. Configuration & Speed Tuning

### 3.1. Connection Pooling
- **Default**: New HTTP connection per request (slow).
- **Optimization**: Use `aiohttp.ClientSession` with a `TCPConnector` that has a high `limit`.
  ```python
  # In AsyncDatabaseManager
  connector = aiohttp.TCPConnector(limit=100) # Allow 100 concurrent connections
  session = aiohttp.ClientSession(connector=connector)
  client = ArangoClient(hosts="...", http_client=session)
  ```

### 3.2. Batch Size
- `CallSyncService` uses batching.
- **Recommendation**:
  - `read_batch_size`: 1000-5000 documents (Fetching data).
  - `write_batch_size`: 500-1000 documents (Transactions/Writes).
  - **Too High**: Request timeouts or memory pressure.
  - **Too Low**: Network latency dominates.

### 3.3. Indexing
- **Current**: Relying on `node_type`, `qname`.
- **Missing**:
  - **Edge Index**: automatically created on `_from` and `_to`.
  - **Target Lookup**: Ensure `targets_edges` has a persistent index if you filter on other properties, but standard traversal uses the edge index.
- **Action**: Check if specialized indices are needed for `qname` lookups if they are slow.

## 4. Query Refactoring Cheat Sheet

| Query Pattern | Optimization |
|---------------|--------------|
| `FOR v, e, p IN 1..100 ...` | Use `PRUNE` early to stop traversal branches that aren't fruitful. |
| `RETURN v` | `RETURN { id: v._id, type: v.node_type }` (Reduce payload size). |
| `list(cursor)` | `async for doc in cursor` (Streaming). |
| `[repo.find(x) for x in ids]` | `repo.find_batch(ids)` (Reduce roundtrips). |

## 5. Specific Fix for `get_containment_tree`
To fix the specific "slowness" mentioned:

1.  **Backend**: Change to async generator.
2.  **Frontend/API**: If this feeds a UI, enable **Pagination**.
    - Instead of depth 100, fetch depth 1 or 2 (immediate children).
    - When user expands a folder, fetch the next level (Lazy Loading).
    - This changes the query from `1..100` to `1..1`.
    - **Speedup**: From 2s to 20ms.

```aql
// Lazy Load Query (Depth 1)
FOR v, e IN 1..1 OUTBOUND @start_node_id @@contains_collection
    RETURN { node: v, edge: e, hasChildren: LENGTH(FOR c IN 1..1 OUTBOUND v @@contains_collection LIMIT 1 RETURN 1) > 0 }
```
This query returns immediate children AND a flag if they have children, allowing the UI to show an expand arrow without fetching the whole subtree.
