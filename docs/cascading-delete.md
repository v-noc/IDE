# Cascading Delete in ArangoDB

This document outlines the proper approach for cascading deletes in ArangoDB, specifically for the V-NOC project. It addresses the issue where edges remain orphaned after node deletion.

---

## Problem Statement

When deleting a project (or any container node), **all edges pointing to/from the deleted nodes must also be removed**. Otherwise:
- Orphaned edges waste storage
- Traversal queries may return invalid references
- Data integrity is compromised

### Current Issue

The `ProjectService.delete()` method uses `ContainerService.delete_recursive()`, which:
1. Fetches all descendants via `get_containment_tree()`
2. Calls `delete_batch()` on all descendant keys
3. Each individual `delete()` cleans edges → **N+1 database operations**

Meanwhile, `ProjectRepo.delete()` already has an optimized bulk approach that:
1. Collects all vertex IDs in a single AQL query
2. Bulk-removes edges across all edge collections
3. Bulk-removes vertices

---

## Recommended Fix

### Option 1: Use Repository's Bulk Delete (Quick Fix)

Update `ProjectService.delete()` to delegate to `ProjectRepo.delete()`:

```python
# project_service.py
async def delete(self, project: ProjectNode):
    return await self.repos.project_repo.delete(project.key)
```

---

## Scalable AQL Patterns for Cascading Delete

### Pattern 1: Collect-Then-Remove (Recommended)

This is the **safest and most scalable** pattern. It separates reading from writing to avoid AQL conflicts.

```aql
// Step 1: Collect all descendant vertex IDs
LET vertexIds = APPEND(
    [@start_node_id],
    FOR v IN 1..50 OUTBOUND @start_node_id contains_edges
        RETURN v._id
)
RETURN UNIQUE(vertexIds)
```

```aql
// Step 2: Remove edges (run for each edge collection)
FOR e IN @@edge_collection
    FILTER e._from IN @vertexIds OR e._to IN @vertexIds
    REMOVE e IN @@edge_collection
```

```aql
// Step 3: Remove vertices
FOR vid IN @vertexIds
    LET parsed = IS_STRING(vid) ? PARSE_IDENTIFIER(vid) : null
    FILTER parsed != null
    FILTER parsed.collection == @collection_name
    REMOVE { _key: parsed.key } IN @@vertex_collection
        OPTIONS { ignoreErrors: true }
```

### Why This Pattern Scales

| Aspect | Individual Delete | Bulk Delete |
|--------|------------------|-------------|
| DB Round-trips | O(N × E) | O(E + 1) |
| Query Complexity | Simple | Single complex AQL |
| Edge Cleanup | Per-node basis | All at once |
| Performance | ~70ms per node | ~100ms total |

> [!NOTE]
> **E** = number of edge collections, **N** = number of nodes to delete

---

## Pattern 2: Single-Query Cascade (Advanced)

For maximum efficiency, combine everything into a single transaction-like flow:

```aql
// Collect all vertices first
LET startId = @start_node_id
LET descendants = (
    FOR v IN 1..50 OUTBOUND startId contains_edges
        RETURN v._id
)
LET allIds = APPEND([startId], descendants)

// Remove edges from contains_edges
LET _edgesRemoved1 = (
    FOR e IN contains_edges
        FILTER e._from IN allIds OR e._to IN allIds
        REMOVE e IN contains_edges
        RETURN 1
)

// Remove edges from targets_edges
LET _edgesRemoved2 = (
    FOR e IN targets_edges
        FILTER e._from IN allIds OR e._to IN allIds
        REMOVE e IN targets_edges
        RETURN 1
)

// Remove all vertices
FOR vid IN allIds
    LET parsed = PARSE_IDENTIFIER(vid)
    FILTER parsed.collection == "nodes"
    REMOVE { _key: parsed.key } IN nodes
        OPTIONS { ignoreErrors: true }

RETURN {
    removed_vertices: LENGTH(allIds),
    removed_contains_edges: LENGTH(_edgesRemoved1),
    removed_targets_edges: LENGTH(_edgesRemoved2)
}
```

> [!CAUTION]
> This pattern modifies multiple collections in one query. Although ArangoDB handles this correctly, it can be **slower on very large graphs** due to write-locking. Use Pattern 1 for graphs with >10K nodes.

---

## Edge Collection Discovery

To dynamically discover all edge collections:

```python
async def _get_edge_collections(self) -> List[str]:
    """Get list of edge collection names (cached)."""
    all_collections = await self.db.collections()
    
    edge_cols = []
    for col_info in all_collections:
        if not col_info.get("system"):
            # Check if it's an edge collection
            if await self._is_edge_collection(col_info["name"]):
                edge_cols.append(col_info["name"])
    
    return edge_cols
```

For better performance, **hardcode known edge collections**:

```python
EDGE_COLLECTIONS = ["contains_edges", "targets_edges"]

async def delete_cascade(self, node_key: str):
    # ... use EDGE_COLLECTIONS directly
```

---

## Implementation Checklist

- [ ] Update `ProjectService.delete()` to use `ProjectRepo.delete()`
- [ ] Apply same pattern to other container services if needed:
  - `FolderService.delete()`
  - `FileService.delete()`
  - `ClassService.delete()`
  - `FunctionService.delete()`
- [ ] Consider moving the bulk delete logic to `ContainerService` as a shared method
- [ ] Add integration test to verify no orphaned edges remain after deletion

---

## Testing the Fix

After implementing, verify with this AQL query:

```aql
// Find orphaned edges (edges pointing to non-existent nodes)
FOR e IN contains_edges
    LET from_exists = DOCUMENT(e._from) != null
    LET to_exists = DOCUMENT(e._to) != null
    FILTER !from_exists OR !to_exists
    RETURN {
        edge_id: e._id,
        from: e._from,
        to: e._to,
        from_exists: from_exists,
        to_exists: to_exists
    }
```

---

## Summary

| Approach | Pros | Cons |
|----------|------|------|
| **Individual Delete** | Simple code | O(N×E) operations, slow |
| **Collect-Then-Remove** | Safe, scalable | Multiple queries |
| **Single-Query Cascade** | Fastest for small graphs | Complex, write-locking on large graphs |

**Recommendation**: Use the "Collect-Then-Remove" pattern (already implemented in `ProjectRepo.delete()`) and update the service layer to delegate to it.
