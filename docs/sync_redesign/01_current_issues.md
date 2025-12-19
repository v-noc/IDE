# Current System Issues

## Architecture Overview

### Current Flow
```
Discovery Phase:
  ├── Scanner: Scans disk, computes checksums
  ├── ChangeDetector: Compares disk vs DB by path + checksum
  └── Output: ChangeSet(new, modified, deleted files/folders)

Sync Phase:
  ├── ScopeSyncService: Recursively syncs scopes with versioning
  ├── Version Strategy: Timestamp-based version on nodes/edges
  └── Filtering: Skip unchanged files/folders in incremental mode
```

## Issue #1: Version Propagation Problem

### Problem Statement
When a file is removed from a folder, all sibling files must be re-synced to update their parent's version, even if they haven't changed.

### Root Cause
The `current_version` field on nodes is used for version-based filtering in `get_containment_tree`:

```aql
PRUNE (v.current_version < parent.current_version)
```

This means if a parent folder's version changes (e.g., due to child deletion), all children need their versions updated to remain visible in queries.

### Example Scenario
```
project/
  src/
    file1.py  (version: 100)
    file2.py  (version: 100)
    file3.py  (version: 100)

# User deletes file2.py
# Expected: Only file2.py is processed
# Actual: src/ version becomes 101
#         file1.py and file3.py must update to version 101
#         Otherwise they're "pruned" by version filter
```

### Impact
**User Quote**: *"Creates friction at MVP stage"*

- Processing hundreds of unchanged files just because one sibling was deleted
- Increases sync time exponentially with project size
- Database write amplification
- Unnecessary network traffic

### Code Evidence
**Location**: `src/backend/app/core/repository/base/node_repo.py:119-132`

```python
FOR v, e, p IN 1..@max_depth OUTBOUND @start_node_id
    @@contains_collection
    
    PRUNE (
        (v.current_version != null ? v.current_version : 0) 
        < 
        (LENGTH(p.vertices) >= 2 
            ? (p.vertices[-2].current_version != null ? p.vertices[-2].current_version : 0)
            : start_ver
        )
    )
```

## Issue #2: Path-Based Change Detection (No Rename Support)

### Problem Statement
File and folder renames are detected as `deleted + new`, causing loss of history and IDs.

### Current Logic
**Location**: `src/backend/app/core/parser/graph_builder/discovery/change_detector.py:57-67`

```python
for path in all_paths:
    in_disk = path in current_files
    in_db = path in db_state

    if in_disk and not in_db:
        new_files.append(path)  # Could be a rename!
    elif in_db and not in_disk:
        deleted_files.append(path)  # Could be a rename!
    elif in_disk and in_db:
        if current_files[path] != db_state[path]:
            modified_files.append(path)
```

### Example Scenario
```python
# Before: File exists at src/old_name.py (ID: abc-123)
# After:  File renamed to src/new_name.py

# Current Detection:
change_set = ChangeSet(
    deleted_files=['src/old_name.py'],
    new_files=['src/new_name.py'],
    modified_files=[]
)

# Result:
# - Scope abc-123 is deleted from DB
# - New scope xyz-456 is created
# - All child scopes (functions, classes) are recreated
# - Call graph connections to this file are lost
```

### Impact
- **History Loss**: File's identity (ID) is not preserved
- **Cascade Deletion**: All child scopes (functions, classes) are deleted
- **Graph Corruption**: Incoming references (calls to functions in this file) become orphaned
- **Performance**: Re-parsing and re-syncing unchanged content

### Why This Happens
The system uses `file_path` as the unique identifier:
- **Database**: `scope.file_path = "src/old_name.py"`
- **Disk**: File at `"src/new_name.py"`
- **Match**: No match found → Interpreted as delete + create

## Issue #3: Shallow Nested Change Detection

### Problem Statement
**User Quote**: *"The current traverse does not handle it well, it only checks top level changes"*

Change detection only compares top-level file paths, not the full folder hierarchy.

### Example Scenario
```
project/
  src/          # folder exists in DB
    nested/     # NEW folder on disk (not in DB)
      deep/     # NEW folder on disk (not in DB)
        file.py # NEW file on disk (not in DB)
```

### Current Behavior
**Location**: `change_detector.py:69-77`

```python
current_folder_paths = current_folders
new_folders = [
    folder for folder in current_folder_paths
    if folder not in db_folder_paths
]
deleted_folders = [
    folder for folder in db_folder_paths
    if folder not in current_folder_paths
]
```

### What Works ✓
- `file.py` is detected as `new_files`

### What Fails ✗
- If `scanner.py` only returns changed top-level folders
- `nested/` and `deep/` may not appear in `new_folders`
- When sync tries to create `file.py`, parent folder `deep/` doesn't exist in DB
- Results in orphaned nodes or sync failures

### Root Cause
The logic assumes the scanner provides ALL folders (nested included). If the scanner is not fully recursive, or if it filters folders, the nested ones are missed.

## Issue #4: Inconsistent Folder Version Updates

### Problem Statement  
**User Quote**: *"The way it checks the changed folder is wrong"*

Folders are only marked for sync if they appear in `new_folders` or `deleted_folders`, but not when their children are modified.

### Current Logic
**Location**: `scope_sync.py:103-108`

```python
elif scope.type == ScopeType.FOLDER:
    is_in_change_set = (
        scope.file_path in change_set.new_folders or
        scope.file_path in change_set.deleted_folders
    )
```

### Missing Cases

#### Case 1: Child File Modified
```
project/
  src/               # Folder NOT in change_set
    modified_file.py # File IS in modified_files
```
**Expected**: `src/` folder should update its version (child changed)
**Actual**: `src/` folder is skipped (not in `new_folders` or `deleted_folders`)

#### Case 2: Folder Rename
```
project/
  old_name/   # Detected as deleted
  new_name/   # Detected as new
```
**Expected**: Treated as rename (preserve ID and children)
**Actual**: Entire subtree deleted and recreated

#### Case 3: Nested Folder Creation
```
project/
  src/existing/new_subfolder/  # new_subfolder is new
```
**Expected**: `new_subfolder` in `new_folders`
**Actual**: May be missed if scanner doesn't recurse properly

### Impact
- Folder metadata (version, timestamps) becomes stale
- Tree queries may return outdated folder structures
- Parent-child relationships in the graph become inconsistent

## Summary Table

| Issue | Impact | Why It Happens | MVP Blocker? |
|-------|--------|----------------|--------------|
| **Version Propagation** | Re-syncs unchanged files | Version filtering in queries requires cascading updates | Yes - Performance |
| **No Rename Detection** | Deletes and recreates on rename | Path-based identity | Yes - Data loss |
| **Shallow Nested Detection** | Misses deep folder structures | Incomplete folder scanning | Yes - Correctness |
| **Folder Version Inconsistency** | Stale folder metadata | Folder changes only on create/delete | Medium - UX |

## Next Steps
See [02_id_tracking_solution.md](02_id_tracking_solution.md) for the proposed solution to these issues.
