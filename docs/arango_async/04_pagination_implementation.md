# Pagination & Streaming Strategies

## 1. The Core Problem
In the synchronous code, the common pattern is:
```python
cursor = db.aql.execute(query)
results = list(cursor)  # Consumes EVERYTHING into RAM
return results
```
For `get_containment_tree` or large datasets, this causes:
1.  **Latency**: User waits until the *last* item is fetched before seeing the *first*.
2.  **Memory**: 100k nodes = 100k dicts in memory.
3.  **Blocking**: The GIL is held or the thread is blocked during network I/O.

## 2. Async Cursor Streaming (The Fix)

### 2.1. Basic Streaming
In `python-arango-async`, cursors are asynchronous iterators. You should process items as they arrive.

```python
async def process_large_dataset():
    # batch_size=1000 means the driver fetches 1000 docs at a time from server
    cursor = await db.aql.execute(query, batch_size=1000)
    
    async for doc in cursor:
        await process_single_document(doc)
        # The app remains responsive!
```

### 2.2. Stream to API Response
If you use FastAPI or similar, you can stream the response directly to the client.

```python
from fastapi.responses import StreamingResponse

async def get_tree_stream():
    cursor = await db.aql.execute("FOR v IN ... RETURN v", batch_size=500)
    
    async def output_generator():
        yield "["
        first = True
        async for doc in cursor:
            if not first: yield ","
            yield json.dumps(doc)
            first = False
        yield "]"

    return StreamingResponse(output_generator(), media_type="application/json")
```

## 3. Pagination Approaches

### 3.1. Offset Pagination (Simple but Slow)
```aql
FOR doc IN collection
    LIMIT @offset, @limit
    RETURN doc
```
- **Pros**: Easy to implement.
- **Cons**: Performance degrades linearly. To get items 10,000 to 10,010, the DB must scan 10,010 items.

### 3.2. Cursor/Keyset Pagination (Fast & Recommended)
Instead of skipping X items, valid "start after" the last item you saw.

**Sort by ID:**
```aql
FOR doc IN collection
    FILTER doc._key > @last_seen_key
    SORT doc._key ASC
    LIMIT @limit
    RETURN doc
```
- **Pros**: $O(1)$ complexity with index. Constant speed regardless of depth.
- **Cons**: Requires keeping track of tokens/keys.

## 4. Solving `get_containment_tree` Slowness

The user specifically mentioned `get_containment_tree` is slow. It likely returns a massive JSON structure.

### Strategy A: Frontend Lazy Loading (Best UX)
**Don't fetch the whole tree.**
1.  **Initial Call**: Fetch internal roots + Depth 1.
2.  **User Action**: User clicks ">" on "src".
3.  **Subsequent Call**: Fetch children of "src".

**Old Query**: `1..100 OUTBOUND`
**New Query**: `1..1 OUTBOUND`

### Strategy B: Graph Layout Streaming
If you absolutely need the whole graph for a layout algorithm (e.g. Force Directed):

1.  **Node-Link Format**: Return `{ nodes: [...], links: [...] }`.
2.  **Compact Projection**:
    ```aql
    RETURN { id: v._id, p: v.parent_id }
    ```
    Only send IDs and structure. Fetch metadata (labels, icons) purely for the *viewport* nodes later.

### Strategy C: Async Generator Pipeline
Refactor the service to yield chunks of the tree.

```python
# In NodeRepository
async def get_tree_generator(self, root_id):
    query = "FOR v, e, p IN 1..100 ..."
    cursor = await self.db.aql.execute(query, batch_size=5000)
    async for batch in cursor.batch(): # Hypothetical batch iterator or manual chunking
        yield batch
```

## 5. Migration Checklist for Pagination

- [ ] Identify all usage of `list(cursor)`.
- [ ] Identify all API endpoints returning lists > 1000 items.
- [ ] For `get_containment_tree`, implement **Strategy A** (Limit depth) if possible.
- [ ] For Logs/History, implement **Strategy 3.2** (Keyset pagination).
- [ ] Set global default `batch_size` on the Async Orchestrator to avoid timeouts.
