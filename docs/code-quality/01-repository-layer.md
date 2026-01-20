# Repository Layer Analysis

## Overview
Analysis of repository pattern implementation across `file_repo.py`, `folder_repo.py`, `project_repo.py`, `class_repo.py`, `function_repo.py`, `call_repo.py`, and base `node_repo.py`.

---

## 🔴 Critical Issues

### 1. Duplicated `delete_batch` Implementations
**Files**: `file_repo.py:80-91`, `folder_repo.py:82-104`, `class_repo.py:32-43`, `function_repo.py:32-43`

All four repos have **identical** `delete_batch` logic that loops and calls `self.delete()`:

```python
async def delete_batch(self, ids: List[str]) -> bool:
    if not ids:
        return True
    clean_ids = [i.split("/")[-1] if "/" in i else i for i in ids]
    success = True
    for node_id in clean_ids:
        if not await self.delete(node_id):
            success = False
    return success
```

**Problem**: This is 100% duplicated code across 4 files.

**Solution**: Move to `NodeRepository` base class (already has `delete_batch` at line 413 that returns `List[bool]` - but signature differs). Standardize on one implementation.

---

### 2. Duplicated `get_by_qnames` Implementations  
**Files**: `file_repo.py:59-78`, `folder_repo.py:61-80`, `class_repo.py:11-30`, `function_repo.py:11-30`

Nearly identical queries differing only by `node_type` filter:

```python
async def get_by_qnames(self, qnames: List[str]) -> Dict[str, NodeType]:
    query = """
        FOR n IN @@collection
            FILTER n.qname IN @qnames
            FILTER n.node_type == "file"  # Only this line differs!
            RETURN n
    """
```

**Solution**: Create generic `get_by_qnames(qnames, node_type)` in `NodeRepository`.

---

### 3. Duplicated `get_by_ids` Implementations
**Files**: `file_repo.py:36-57`, `folder_repo.py:37-59`

Same pattern as above - identical logic with different `node_type` filter.

**Solution**: Add to `NodeRepository` base class.

---

## 🟡 Design Issues

### 4. Inconsistent Return Types in `delete_batch`
| Repository | Method | Return Type |
|------------|--------|-------------|
| `NodeRepository` | `delete_batch` | `List[bool]` |
| `FileRepo` | `delete_batch` | `bool` |
| `FolderRepo` | `delete_batch` | `bool` |

**Problem**: Parent returns per-item success, children return aggregate boolean.

---

### 5. Redundant Method: `find_call_by_pair`
**File**: `call_repo.py:89-94`

```python
async def find_call_by_pair(self, parent_id: str, target_id: str):
    return await self.find_call_by_target_parent(target_id, parent_id)
```

This is a **1-line wrapper** that just swaps argument order. Consider removing or documenting the purpose.

---

### 6. Similar Methods Without Abstraction
**File**: `call_repo.py`

| Method | Lines | Purpose |
|--------|-------|---------|
| `count_recursive_calls_upward` | 238-284 | Single pair count |
| `count_recursive_calls_upward_batch` | 286-344 | Batch version |
| `find_call_by_target_parent` | 138-174 | Single pair lookup |
| `find_calls_by_target_parent_batch` | 176-236 | Batch version |

**Pattern**: Each operation has single + batch version with duplicated query logic.

**Solution**: Use a single batch method and have single version call it with `[pair]`.

---

### 7. Unused / Redundant Helper in `call_repo.py`
**Lines 96-111**: `find_calls_by_targets` and `count_recursion_depth` are thin wrappers:

```python
async def find_calls_by_targets(self, target_pairs):
    return await self.find_calls_by_target_parent_batch(target_pairs)

async def count_recursion_depth(self, parent_id, target_id):
    return await self.count_recursive_calls_upward(parent_id, target_id)
```

**Recommendation**: Either remove wrappers or keep only the semantic names.

---

## 🟢 Improvement Recommendations

### Step 1: Consolidate to Base Repository

Add these methods to `NodeRepository`:

```python
# In node_repo.py

async def get_by_ids(self, ids: List[str], node_type: Optional[str] = None) -> Dict[str, T]:
    """Generic batch ID fetch with optional type filter."""
    
async def get_by_qnames(self, qnames: List[str], node_type: Optional[str] = None) -> Dict[str, T]:
    """Generic batch qname fetch with optional type filter."""

async def delete_batch(self, keys: List[str]) -> List[bool]:
    """Keep existing implementation; remove from child repos."""
```

### Step 2: Remove Duplicates from Child Repos

Delete these methods from `FileRepo`, `FolderRepo`, `ClassRepo`, `FunctionRepo`:
- `delete_batch`
- `get_by_qnames` 
- `get_by_ids`

### Step 3: Simplify CallRepo

```python
# Before: 4 methods
find_call_by_target_parent()
find_calls_by_target_parent_batch()
count_recursive_calls_upward()
count_recursive_calls_upward_batch()

# After: 2 methods (single calls batch with [pair])
find_calls_by_target_parent_batch()
count_recursive_calls_upward_batch()
```

---

## Summary

| Category | Count |
|----------|-------|
| Duplicated methods | 12+ |
| Redundant wrappers | 3 |
| Inconsistent signatures | 2 |
| **Estimated LOC reduction** | **~150 lines** |
