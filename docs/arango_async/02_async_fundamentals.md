# Async Fundamentals

## Introduction

This document covers the core async concepts you need to understand for the ArangoDB migration. If you're new to async Python, this is your starting point.

---

## The Problem with Synchronous Code

### Blocking I/O Example

```python
# Synchronous (current)
def fetch_user(user_id):
    user = db.users.get(user_id)  # ← Blocks for 10ms (waiting for DB)
    return user

def get_users(user_ids):
    users = []
    for uid in user_ids:  # Sequential!
        users.append(fetch_user(uid))  # Each blocks for 10ms
    return users

# For 100 users: 100 × 10ms = 1 second wasted waiting!
```

**Timeline**:
```
User 1:  [Wait 10ms...........................] Done
User 2:                                        [Wait 10ms...] Done
User 3:                                                      [Wait 10ms...] Done
...
Total: 1 second (all sequential)
```

### With Async (Concurrent)

```python
# Asynchronous (future)
async def fetch_user(user_id):
    user = await db.users.get(user_id)  # ← Non-blocking: yields control
    return user

async def get_users(user_ids):
    tasks = [fetch_user(uid) for uid in user_ids]  # Create tasks (doesn't execute yet)
    users = await asyncio.gather(*tasks)  # Execute all concurrently!
    return users

# For 100 users: max(10ms) ≈ 10-20ms (mostly parallel!)
```

**Timeline**:
```
User 1:  [Wait 10ms] Done
User 2:  [Wait 10ms] Done
User 3:  [Wait 10ms] Done
...all at the same time!
Total: 20ms (concurrent)
```

---

## Core Concepts

### 1. The Event Loop

Think of it as a task scheduler that manages async operations.

```python
import asyncio

async def main():
    print("Starting...")
    await asyncio.sleep(1)  # Yields to event loop
    print("Done!")

# Run the event loop
asyncio.run(main())  # This creates and manages the event loop
```

**Key Points**:
- Only **one** event loop per thread
- The loop switches between tasks while they wait for I/O
- CPU-bound operations still block (use threading/multiprocessing for those)

### 2. `async` and `await`

**`async def`**: Declares a coroutine function
```python
async def my_coroutine():
    return "Hello"

# Calling it returns a coroutine object (not the result!)
coro = my_coroutine()  # This doesn't execute the function!
result = await coro     # This executes it
```

**`await`**: Pauses execution until the awaitable completes
```python
async def fetch_data():
    data = await db.query("SELECT ...")  # Pause here, let other tasks run
    return data
```

**Rules**:
- Can only `await` inside an `async def` function
- Can only call `async def` functions with `await` or by scheduling them

### 3. Coroutines vs Functions

| Aspect | Regular Function | Coroutine (`async def`) |
|--------|-----------------|-------------------------|
| **Declaration** | `def func():` | `async def func():` |
| **Call** | `result = func()` | `result = await func()` |
| **Return** | Actual value | Coroutine object |
| **Blocking** | Yes | No (cooperative multitasking) |

---

## Python Arango Async API

### Client Initialization

**Sync (current)**:
```python
from arango import ArangoClient

client = ArangoClient(hosts='http://localhost:8529')
db = client.db('my_db', username='root', password='')
```

**Async (future)**:
```python
from arangoasync import ArangoClient
from arangoasync.auth import Auth

async def get_db():
    async with ArangoClient(hosts='http://localhost:8529') as client:
        auth = Auth(username='root', password='')
        db = await client.db('my_db', auth=auth)
        return db
```

**Key Differences**:
1. `async with` for proper resource cleanup
2. `await client.db()` instead of direct call
3. Must be inside an async function

### Query Execution

**Sync (current)**:
```python
cursor = db.aql.execute("FOR doc IN collection RETURN doc")
results = list(cursor)  # Blocks until all docs loaded
```

**Async (future)**:
```python
cursor = await db.aql.execute("FOR doc IN collection RETURN doc")
results = []
async for doc in cursor:  # ← Streaming!
    results.append(doc)
    # Can process each doc as it arrives!
```

### CRUD Operations

**Sync**:
```python
collection = db.collection('users')
doc = collection.insert({'name': 'Alice'})
```

**Async**:
```python
collection = await db.collection('users')  # Get collection handle
doc = await collection.insert({'name': 'Alice'})  # Await the insert
```

---

## Concurrency Patterns

### Pattern 1: `asyncio.gather()` (Parallel Execution)

**Use Case**: Execute multiple independent operations concurrently

```python
async def fetch_user(user_id):
    return await db.users.get(user_id)

async def fetch_all_users(user_ids):
    # Create list of coroutines
    tasks = [fetch_user(uid) for uid in user_ids]
    
    # Execute all concurrently
    results = await asyncio.gather(*tasks)
    
    return results

# Usage
user_ids = [1, 2, 3, 4, 5]
users = await fetch_all_users(user_ids)
```

**Timeline**:
```
fetch_user(1): [--------] Done
fetch_user(2): [--------] Done
fetch_user(3): [--------] Done
fetch_user(4): [--------] Done
fetch_user(5): [--------] Done
Total: One query time (all parallel!)
```

### Pattern 2: `asyncio.Semaphore` (Controlled Concurrency)

**Use Case**: Limit number of concurrent operations (don't overwhelm DB)

```python
async def fetch_user_with_limit(user_id, semaphore):
    async with semaphore:  # Acquire semaphore
        return await db.users.get(user_id)
    # Semaphore automatically released

async def fetch_all_users(user_ids, max_concurrent=10):
    semaphore = asyncio.Semaphore(max_concurrent)
    
    tasks = [
        fetch_user_with_limit(uid, semaphore)
        for uid in user_ids
    ]
    
    return await asyncio.gather(*tasks)

# Only 10 queries run at a time, even if user_ids has 1000 items
```

**Why?**: Prevents overwhelming the database connection pool.

### Pattern 3: `asyncio.create_task()` (Background Tasks)

**Use Case**: Fire-and-forget operations

```python
async def log_access(user_id):
    await db.access_logs.insert({'user_id': user_id, 'timestamp': now()})

async def handle_request(user_id):
    # Get user (we need this)
    user = await db.users.get(user_id)
    
    # Log access in background (don't wait)
    asyncio.create_task(log_access(user_id))
    
    # Return immediately
    return user
```

**Warning**: Ensure the task completes before program exit!

### Pattern 4: `async for` (Streaming)

**Use Case**: Process results as they arrive (don't buffer everything)

```python
async def process_large_dataset():
    cursor = await db.aql.execute(
        "FOR doc IN huge_collection RETURN doc",
        batch_size=1000  # Fetch 1000 at a time
    )
    
    async for doc in cursor:
        await process_document(doc)  # Process one by one
        # Memory usage stays constant!
```

---

## Connection Pooling

### The Problem

**Sync (current)**:
- Each request creates a new HTTP connection
- Connection overhead: ~5-10ms per query
- No reuse

**Async (with pooling)**:
- Pre-create a pool of connections
- Reuse connections across queries
- Connection overhead amortized

### Implementation

```python
import aiohttp
from arangoasync import ArangoClient

async def create_client():
    # Create HTTP session with connection pooling
    connector = aiohttp.TCPConnector(
        limit=100,              # Max 100 connections total
        limit_per_host=50,      # Max 50 per host
        ttl_dns_cache=300       # DNS cache for 5 min
    )
    
    session = aiohttp.ClientSession(connector=connector)
    
    client = ArangoClient(
        hosts='http://localhost:8529',
        http_client=session  # Use our custom session
    )
    
    return client, session

async def main():
    client, session = await create_client()
    
    try:
        # Use client for all operations
        db = await client.db('my_db', auth=...)
        # ... do work ...
    finally:
        # Clean up
        await session.close()
        await client.close()
```

---

## Error Handling

### Async Try-Except

```python
async def fetch_user_safe(user_id):
    try:
        user = await db.users.get(user_id)
        return user
    except DocumentNotFoundError:
        return None
    except ArangoServerError as e:
        logger.error(f"DB error: {e}")
        raise
```

### Gather with `return_exceptions`

```python
async def fetch_users_safe(user_ids):
    tasks = [fetch_user(uid) for uid in user_ids]
    
    # Returns both successes and exceptions as results
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter successes
    users = [r for r in results if not isinstance(r, Exception)]
    
    # Log errors
    errors = [r for r in results if isinstance(r, Exception)]
    for err in errors:
        logger.error(f"Failed to fetch user: {err}")
    
    return users
```

---

## Cursors and Streaming

### Problem: Buffering vs Streaming

**Sync (current) - Full Buffering**:
```python
cursor = db.aql.execute("FOR doc IN collection RETURN doc")
results = list(cursor)  # Loads ALL docs into memory
```

**Memory**: 10,000 docs × 1KB = **10 MB**

**Async - Streaming**:
```python
cursor = await db.aql.execute("FOR doc IN collection RETURN doc", batch_size=100)

async for doc in cursor:
    process(doc)  # Process one at a time
    # Only 100 docs in memory at a time
```

**Memory**: 100 docs × 1KB = **100 KB** (100x less!)

### Batch Processing

```python
async def process_in_batches():
    cursor = await db.aql.execute(
        "FOR doc IN collection RETURN doc",
        batch_size=1000
    )
    
    batch = []
    async for doc in cursor:
        batch.append(doc)
        
        if len(batch) >= 1000:
            await process_batch(batch)  # Process batch
            batch = []  # Reset
    
    if batch:  # Process final partial batch
        await process_batch(batch)
```

---

## Testing Async Code

### Pytest with `pytest-asyncio`

```python
import pytest

@pytest.mark.asyncio
async def test_fetch_user():
    user_id = "test-123"
    user = await fetch_user(user_id)
    assert user.id == user_id
```

### Running in REPL

```python
# In IPython or Jupyter
await my_async_function()  # Works directly!

# In standard Python REPL
import asyncio
asyncio.run(my_async_function())
```

---

## Common Pitfalls

### 1. Forgetting `await`

```python
# ❌ WRONG
async def bad():
    result = db.query("SELECT ...")  # Returns coroutine object!
    return result  # NOT the actual data

# ✅ CORRECT
async def good():
    result = await db.query("SELECT ...")  # Executes and waits
    return result
```

### 2. Blocking in Async Function

```python
# ❌ BAD (blocks event loop)
async def bad():
    import time
    time.sleep(1)  # ← BLOCKS entire event loop!
    return "done"

# ✅ GOOD
async def good():
    await asyncio.sleep(1)  # ← Yields to event loop
    return "done"
```

### 3. Not Using Context Managers

```python
# ❌ RISKY (connection may not close)
async def bad():
    client = ArangoClient(...)
    db = await client.db(...)
    # ... do work ...
    # Forgot to close!

# ✅ SAFE
async def good():
    async with ArangoClient(...) as client:
        db = await client.db(...)
        # ... do work ...
    # Automatically closed
```

### 4. Too Much Concurrency

```python
# ❌ BAD (spawns 10,000 tasks!)
async def bad(ids):
    tasks = [fetch(id) for id in ids]  # If ids has 10k items...
    return await asyncio.gather(*tasks)  # Connection pool exhausted!

# ✅ GOOD (limits concurrency)
async def good(ids):
    semaphore = asyncio.Semaphore(50)  # Max 50 concurrent
    
    async def fetch_limited(id):
        async with semaphore:
            return await fetch(id)
    
    tasks = [fetch_limited(id) for id in ids]
    return await asyncio.gather(*tasks)
```

---

## Migration Checklist

Before migrating to async, ensure you understand:

- [ ] `async def` and `await` keywords
- [ ] Event loop concept
- [ ] `asyncio.gather()` for concurrency
- [ ] `async with` context managers
- [ ] `async for` for iteration
- [ ] Connection pooling benefits
- [ ] When to use `Semaphore` for limiting
- [ ] Streaming vs buffering cursors

---

## Next Steps

Now that you understand async fundamentals, proceed to:
- [03_query_optimization.md](03_query_optimization.md) - Apply async to specific queries
- [05_migration_guide.md](05_migration_guide.md) - Step-by-step migration process
