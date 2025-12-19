# ArangoDB Async Migration Master Plan

## 1. Executive Summary
This document outlines the comprehensive strategy for migrating the `v-noc` backend from the synchronous `python-arango` driver to the asynchronous `python-arango-async` driver. This migration is critical for improving performance, handling high-concurrency graph building operations, and preventing blocking I/O during large data syncs.

## 2. Architecture & Dependencies

### Current State
- **Driver**: `python-arango` (Synchronous)
- **Pattern**: Blocking AQL queries, sequential processing in loops.
- **Bottlenecks**: `CallSyncService` and `GraphBuilderOrchestrator` block the main thread during heavy DB writes/reads.

### Future State
- **Driver**: `python-arango-async`
- **Pattern**: `async/await` throughout the stack. Concurrent batch processing using `asyncio.gather`.
- **Concurrency**: Connection pooling and async cursors.

### New Dependencies
Update `pyproject.toml` to include:
```toml
[tool.poetry.dependencies]
python-arango-async = "^1.0.0"  # Check latest version
aiohttp = "^3.9.0"             # Underlying transport
```

## 3. Step-by-Step Migration Plan

### Phase 1: Database Connection & Configuration
**Goal**: Establish async client lifecycle management.

1.  **Create `AsyncDatabaseManager`**:
    - Replacing the sync `StandardDatabase` initialization.
    - Implement an `async context manager` for the client.
    - **Key Change**: `python-arango-async` requires `async with` context for clients and cursors.

2.  **Update `Repositories` Container**:
    - The `Repositories` class currently holds synchronous collections.
    - **Refactor**: It must accept an `AsyncDatabase` instance.
    - **Warning**: All repository `__init__` methods usually just store the DB reference. This is safe, but `super().__init__` in `BaseRepository` might need checks.

### Phase 2: Base Repository Layer
**Location**: `src/backend/app/core/repository/base/`

1.  **`BaseRepository` (`base_collection.py`)**:
    - `find()`, `find_one()`, `create()`, `update()`, `delete()` must become `async`.
    - **Example**:
      ```python
      # Old
      def find_one(self, filters):
          return self.collection.find(filters)

      # New
      async def find_one(self, filters):
          # Collections are accessed via awaitable methods or properties depending on driver version
          # In python-arango-async, some operations are direct awaitables.
          cursor = await self.db.aql.execute(query, ...)
          return await cursor.next()
      ```

2.  **`NodeRepository` (`node_repo.py`)**:
    - Update `get_parent`, `get_containment_tree`.
    - **Optimization**: `get_containment_tree` uses a large graph traversal. This will benefit significantly from async streaming of the cursor.

### Phase 3: Domain Repositories
**Location**: `src/backend/app/core/repository/code_elements/` & `log_repo.py`

1.  **`CallRepo`**:
    - `find_call_by_target_parent`: High frequency call.
    - `count_recursive_calls_upward`: Heavy graph traversal.
    - **Strategy**: Convert all methods to `async def`.

2.  **`LogRepo`**:
    - `create_batch`: Currently iterates or sends batch.
    - **Async Opportunity**: Use `await asyncio.gather(*[repo.create(log) for log in logs])` if true batching API isn't used, OR use the async batch import API if available.

### Phase 4: Service Layer & Business Logic
**Location**: `src/backend/app/core/services/`

1.  **Services (`ContainerService`, `CallService`, etc.)**:
    - These are the consumers of Repositories.
    - All methods calling repo methods must become `async def`.
    - **Cascade Effect**: This will bubble up to the API controllers / Orchestrator.

### Phase 5: Sync Engine (The Core Work)
**Location**: `src/backend/app/core/parser/graph_builder/sync/`

1.  **`SyncHelpers`**:
    - Update `ensure_contains_edges_batch` and `ensure_targets_edges_batch`.
    - **Big Win**: These are currently sequential or blocking batch calls. Async allows firing off these ensures without blocking the CPU for unrelated tasks.

2.  **`CallSyncService`**:
    - This is the heaviest user of DB.
    - `_batch_sync_calls`, `sync_call_chains`.
    - **Strategy**:
        - Replace loops with `asyncio.TaskGroup` (Python 3.11+) or `asyncio.gather`.
        - **Critical**: Control concurrency limit (e.g. `asyncio.Semaphore(10)`) to avoid overwhelming the DB connection pool.

### Phase 6: Orchestrator
**Location**: `src/backend/app/core/parser/graph_builder/orchestrator.py`

1.  **Main Loop**:
    - `GraphBuilderOrchestrator._process_changes` must be async.
    - The entry point for the background job must run in an event loop.

## 4. Common Pitfalls & Solutions

| Pitfall | Solution |
|---------|----------|
| **Cursor Exhaustion** | Async cursors must be iterated with `async for` or explicit `await cursor.next()`. Don't forget `await`. |
| **Connection Limits** | Use a Semaphore to limit concurrent AQL queries. Don't `gather` 10,000 queries at once. |
| **Context Context** | The `ArangoClient` session must remain open while queries run. Ensure the lifecycle maps to the Orchestrator run. |
| **Pydantic Validation** | Validation is CPU bound. It happens *after* the DB await. This is good; it releases the event loop. |

## 5. Directory Specific Tasks

### `src/backend/app/core/repository`
- [ ] Rename `base_collection.py` -> `async_base_collection.py` (optional, but good for tracking).
- [ ] Convert all AQL execution to `await db.aql.execute(...)`.
- [ ] Convert all cursor iteraction to `async for doc in cursor:`.

### `src/backend/app/core/parser/graph_builder/sync`
- [ ] **SyncHelpers**: Refactor `ensure_*` methods to be async.
- [ ] **CallSync**: Rewrite `sync_call_chains` to use `asyncio.gather` for processing independent scopes.

## 6. Next Steps
Proceed to the **Query Analysis** document to see specific optimizations for your heavy AQL queries.
