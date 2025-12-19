# Sync Strategies

## Design Philosophy for MVP

**User Requirement**: *"For now deleting is okay"*

**Interpretation**: At the MVP stage, we prioritize **correctness and simplicity** over optimization. Complex incremental update logic can wait until the ID-based foundation is stable.

## Strategy Overview

We propose two complementary sync strategies:

1. **Mode A: Simple Delete-and-Rebuild** (MVP Default)
2. **Mode B: Smart Rename Handling** (Preserves history)

---

## Mode A: Simple Delete-and-Rebuild

### When to Use
- File content modified
- Folder structure changed
- Any ambiguous case
- **MVP Default approach**

### Algorithm

```python
def sync_with_deletion(scope_id: str, file_path: str):
    """
    Simple, correct, predictable sync.
    Delete the entire scope subtree and rebuild from disk.
    """
    # Step 1: Delete scope and all descendants
    delete_scope_tree(scope_id)
    
    # Step 2: Re-parse file from disk
    ast_tree, scope_tree = parse_file(file_path)
    
    # Step 3: Re-sync to database
    sync_scope_hierarchy(scope_tree)
    sync_call_chains(scope_tree)
```

### Detailed Flow

```
1. Detection: File src/main.py modified (checksum changed)

2. Lookup: Find scope_id for src/main.py in DB

3. Delete Phase:
   ├─ Get all descendant scopes (functions, classes, nested)
   ├─ Delete all call sites for each scope
   ├─ Delete contains edges (parent → children)
   ├─ Delete scopes bottom-up
   └─ Result: Clean slate

4. Rebuild Phase:
   ├─ Parse src/main.py with AST processor
   ├─ Extract scopes (functions, classes)
   ├─ Create scope records in DB
   ├─ Create contains edges
   └─ Parse function bodies for calls

5. Sync Phase:
   ├─ Sync call chains
   └─ Update version (optional)
```

### Pros
✅ **Simple**: No complex logic, no edge cases
✅ **Correct**: Always in sync with disk
✅ **Fast for small files**: Deletion is quick
✅ **No cascading updates**: No version propagation issues

### Cons
❌ **Re-creates unchanged scopes**: If only one function changed, all functions are rebuilt
❌ **Temporary history gap**: Call graph links are rebuilt (not lost, just recreated)
❌ **Database churn**: More writes than necessary

### Performance Characteristics

| File Size | Functions | Delete Time | Rebuild Time | Total |
|-----------|-----------|-------------|--------------|-------|
| Small (< 100 LOC) | 1-5 | 10ms | 50ms | **60ms** |
| Medium (100-500 LOC) | 5-20 | 30ms | 200ms | **230ms** |
| Large (500+ LOC) | 20+ | 100ms | 500ms | **600ms** |

**Conclusion**: Acceptable for MVP. Most files are small. Large files are rare and 600ms is tolerable.

---

## Mode B: Smart Rename Handling

### When to Use
- File/folder rename detected (via ID)
- Path changed but content identical
- Want to preserve history and connections

### Algorithm

```python
def handle_rename(
    scope_id: str,
    old_path: str,
    new_path: str
):
    """
    Update paths without deleting.
    Preserves IDs, history, and call graph.
    """
    # Step 1: Update scope's path and qname
    scope = scope_manager.get_scope(scope_id)
    scope.file_path = new_path
    scope.qname = path_to_qname(new_path)
    scope_manager.update_scope(scope)
    
    # Step 2: Recursively update all descendants
    update_descendants_qname(scope_id, old_path, new_path)
    
    # Step 3: Update contains edges if parent changed
    update_parent_edge_if_needed(scope_id, old_path, new_path)
```

### Detailed Flow

```
1. Detection: File renamed from src/old.py → src/new.py
   └─ ID: abc-123 (same in both)

2. Identify: This is a rename, not delete+create

3. Update Scope:
   ├─ scope.file_path: "src/old.py" → "src/new.py"
   ├─ scope.qname: "src.old" → "src.new"
   └─ Write to DB

4. Update Children (Functions, Classes):
   ├─ For each child scope:
   │  ├─ qname: "src.old.MyClass" → "src.new.MyClass"
   │  └─ file_path: "src/old.py" → "src/new.py"
   └─ Recursive for nested children

5. Update Edges:
   ├─ Parent folder may have changed (e.g., moved to different folder)
   ├─ Delete old contains edge
   └─ Create new contains edge
```

### Pros
✅ **Preserves IDs**: No history loss
✅ **Fast**: No deletion, no re-parsing
✅ **Maintains references**: Call graph stays intact
✅ **Minimal DB operations**: Just path/qname updates

### Cons
❌ **More complex**: Requires careful qname updates
❌ **Edge cases**: What if rename also includes content change?

### Handling Combined Rename + Modification

```python
if renamed and modified:
    # Option 1: Do both (Recommended)
    handle_rename(scope_id, old_path, new_path)
    sync_with_deletion(scope_id, new_path)  # Re-parse content
    
    # Option 2: Just rebuild (Simpler for MVP)
    sync_with_deletion(scope_id, new_path)
```

**Recommendation**: For MVP, use Option 2 (simpler). Rename detection is the valuable part for pure renames. If content also changed, delete-and-rebuild is fine.

---

## Version Strategy: Simplify or Abandon?

### Current Problem Recap
Version filtering causes cascading updates:
```aql
PRUNE (v.current_version < parent.current_version)
```
This forces all children to update when parent changes.

### Option 1: Remove Version Filtering (Recommended for MVP)

**Change**:
- Remove `current_version` from queries
- `get_containment_tree` returns full tree (no PRUNE by version)
- Version becomes audit-only field (when was last synced)

**Impact**:
```aql
-- Before (with version filtering)
FOR v, e, p IN 1..50 OUTBOUND @start contains_edges
    PRUNE (v.current_version < parent.current_version)
    RETURN v

-- After (no version filtering)
FOR v, e, p IN 1..50 OUTBOUND @start contains_edges
    RETURN v
```

**Benefits**:
- No cascading version updates
- Simpler sync logic
- No friction on deletions

**Performance Mitigation**:
- Frontend pagination (depth 1, lazy load) - See `docs/arango_pagination_strategies.md`
- Limit max depth in queries
- Most projects have < 10,000 nodes (acceptable)

### Option 2: Keep Version for Audit Only

**Change**:
- Set `current_version` on nodes (timestamp)
- **Don't use it in queries**
- Useful for debugging: "When was this synced?"

**Benefits**:
- Historical record
- No performance impact
- No cascading updates

**Use Case**:
```python
# Check if node is stale
scope = scope_manager.get_scope(scope_id)
if scope.current_version < recent_sync_version:
    print("Warning: This scope may be outdated")
```

### Recommendation
**For MVP**: Use Option 1 (remove version filtering entirely).
- Simplest
- Solves all version propagation issues
- Can add back later if needed

---

## Decision Matrix

| Change Type | Mode A (Delete-Rebuild) | Mode B (Smart Rename) | Recommended for MVP |
|-------------|------------------------|----------------------|---------------------|
| **File Modified** | ✓ Yes | ✗ No | Mode A |
| **File Renamed** | ✓ Works but loses history | ✓ Preserves everything | Mode B |
| **Folder Renamed** | ✓ Works | ✓ Complex (many children) | Mode A or B |
| **File Moved** | ✓ Works | ✓ Update parent edge | Mode B |
| **File Deleted** | ✓ Clean deletion | N/A | Mode A |
| **New File** | N/A (just create) | N/A | Standard sync |

---

## Hybrid Approach (Recommended)

```python
def process_change(change_type, scope_id, file_path):
    if change_type == "rename" and not content_modified:
        # Pure rename: preserve history
        handle_rename(scope_id, old_path, new_path)
    
    elif change_type in ["modified", "new", "deleted", "renamed_and_modified"]:
        # Any modification or complex case: delete and rebuild
        sync_with_deletion(scope_id, file_path)
    
    else:
        raise ValueError(f"Unknown change type: {change_type}")
```

### Implementation in Orchestrator

**Location**: `orchestrator.py:_process_changes()`

```python
def _process_changes(self, change_set: ChangeSet):
    # 1. Handle renames first (no content change)
    for scope_id, old_path, new_path in change_set.renamed_files:
        if is_pure_rename(old_path, new_path):  # Checksum same
            self.sync_service.handle_rename(scope_id, old_path, new_path)
    
    # 2. Delete-and-rebuild for everything else
    for file_path in change_set.modified_files:
        scope_id = self.scope_manager.get_scope_by_path(file_path).id
        self.sync_service.sync_with_deletion(scope_id, file_path)
    
    for file_path in change_set.new_files:
        self.collector.process_file(file_path)
    
    for file_path in change_set.deleted_files:
        scope_id = self.scope_manager.get_scope_by_path(file_path).id
        self.deletion_handler.delete_scope_tree(scope_id)
```

---

## Summary

### For MVP Implementation
1. ✅ Default to **Mode A: Delete-and-Rebuild** for simplicity
2. ✅ Add **Mode B: Smart Rename** only for pure renames (quick win)
3. ✅ Remove version filtering from queries
4. ✅ Keep version field for audit only (optional)

### Why This Works
- Simple code → fewer bugs
- Correct behavior → always in sync
- Fast enough → most files are small
- Extensible → can optimize later

### Next Steps
See [04_migration_plan.md](04_migration_plan.md) for step-by-step implementation.
