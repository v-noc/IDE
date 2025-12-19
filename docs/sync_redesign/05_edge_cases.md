# Edge Cases & Solutions

This document covers all edge cases that must be handled correctly in the ID-based sync system.

---

## Edge Case 1: Folder Rename with Files Inside

### Scenario
```
Before:
project/src/old_package/
    ├── __init__.py (Folder ID: folder-123)
    ├── module1.py (ID: file-abc)
    └── module2.py (ID: file-def)

After:
project/src/new_package/
    ├── __init__.py (Folder ID: folder-123)  # Same ID!
    ├── module1.py (ID: file-abc)
    └── module2.py (ID: file-def)
```

### Detection
```python
# Scanner finds:
disk_folders = {
    "folder-123": FolderInfo(path="src/new_package", id="folder-123")
}

# DB has:
db_folders = {
    "folder-123": ScopeModel(file_path="src/old_package", ...)
}

# Result:
renamed_folders = [("folder-123", "src/old_package", "src/new_package")]
```

### Solution

**Algorithm**:
1. Update folder scope's `file_path` and `qname`
2. For each child file:
   - Update `file_path`: Replace path prefix
   - Update `qname`: Replace qname prefix
3. Recursively update nested children

**Code**:
```python
def handle_folder_rename(folder_id: str, old_path: str, new_path: str):
    # 1. Update folder itself
    folder_scope = scope_manager.get_scope(folder_id)
    folder_scope.file_path = new_path
    folder_scope.qname = path_to_qname(new_path)
    scope_manager.update_scope(folder_scope)
    
    # 2. Update all descendants
    descendants = scope_manager.get_descendants(folder_id)
    for child in descendants:
        # Replace old path prefix with new
        child.file_path = child.file_path.replace(old_path, new_path, 1)
        
        # Replace old qname prefix with new
        old_qname = path_to_qname(old_path)
        new_qname = path_to_qname(new_path)
        child.qname = child.qname.replace(old_qname, new_qname, 1)
        
        scope_manager.update_scope(child)
```

### Verification
- [ ] All file IDs preserved
- [ ] All qnames updated correctly
- [ ] Folder hierarchy intact
- [ ] Call graph references maintained

---

## Edge Case 2: File Moved to Different Folder

### Scenario
```
Before:
project/
    src/
        a/
            file.py (ID: file-abc)
    
After:
project/
    src/
        b/
            file.py (ID: file-abc)  # Same ID, different parent!
```

### Detection
```python
# ID matches, path changed
renamed_files = [("file-abc", "src/a/file.py", "src/b/file.py")]
```

### Solution

**Algorithm**:
1. Update file's `file_path` and `qname`
2. Delete old `contains_edge` (from folder `a/`)
3. Create new `contains_edge` (from folder `b/`)
4. Update children qnames

**Code**:
```python
def handle_file_move(file_id: str, old_path: str, new_path: str):
    file_scope = scope_manager.get_scope(file_id)
    
    # 1. Find old and new parent folders
    old_parent = get_parent_folder(old_path)  # "src/a"
    new_parent = get_parent_folder(new_path)  # "src/b"
    
    # 2. Update file scope
    file_scope.file_path = new_path
    file_scope.qname = path_to_qname(new_path)
    scope_manager.update_scope(file_scope)
    
    # 3. Update parent relationship in graph DB
    if old_parent != new_parent:
        old_parent_scope = scope_manager.get_scope_by_path(old_parent)
        new_parent_scope = scope_manager.get_scope_by_path(new_parent)
        
        # Delete old edge
        repos.contains_edges.delete_edge(
            from_id=old_parent_scope.graph_node_id,
            to_id=file_scope.graph_node_id
        )
        
        # Create new edge
        repos.contains_edges.ensure_edge(
            from_id=new_parent_scope.graph_node_id,
            to_id=file_scope.graph_node_id
        )
    
    # 4. Update children qnames
    update_children_qnames(file_id, old_path, new_path)
```

### Verification
- [ ] File ID preserved
- [ ] Parent folder updated in graph
- [ ] Old contains edge deleted
- [ ] New contains edge created
- [ ] Child scopes updated

---

## Edge Case 3: File Without ID (Legacy)

### Scenario
```
# Old file in DB has no ID (migrated from old system)
DB: ScopeModel(id=None, file_path="src/old.py", checksum="abc123")

# On disk:
src/old.py  # Content unchanged, but no ID comment yet
```

### Detection
When scanner extracts IDs:
```python
disk_files = {
    "src/old.py": FileInfo(path="src/old.py", id=None, checksum="abc123")
}
```

### Solution

**Approach**: Treat as "needs ID assignment"

**Algorithm**:
1. Detect files where `disk.id == None` and file exists in DB
2. Generate new UUID for the file
3. Inject ID into disk file
4. Update DB scope with new ID
5. Mark as "modified" to trigger re-sync

**Code**:
```python
def handle_missing_id(file_path: str):
    # 1. Generate ID
    new_id = str(uuid4())
    
    # 2. Inject into file
    content = Path(file_path).read_text()
    new_content = inject_module_id(content, new_id)
    Path(file_path).write_text(new_content)
    
    # 3. Update DB scope
    scope = scope_manager.get_scope_by_path(file_path)
    if scope:
        scope.id = new_id
        scope_manager.update_scope(scope)
    
    logger.info(f"Assigned ID {new_id} to legacy file {file_path}")
```

**When to run**: During first resync after ID system is deployed

### Verification
- [ ] All legacy files get IDs
- [ ] IDs written to disk
- [ ] DB scopes updated
- [ ] No data loss

---

## Edge Case 4: Folder Deleted But File Moved Out

### Scenario
```
Before:
project/src/
    old_folder/  (ID: folder-123)
        file.py  (ID: file-abc)

After:
project/src/
    file.py  (ID: file-abc)  # Moved out before folder deleted
# old_folder/ is gone
```

### Detection
```python
# File renamed (moved)
renamed_files = [("file-abc", "src/old_folder/file.py", "src/file.py")]

# Folder deleted
deleted_folders = ["src/old_folder"]
```

### Solution

**Order of operations matters!**

**Correct Order**:
1. Process file renames FIRST
2. Process folder deletions SECOND

**Algorithm**:
```python
def process_changes(change_set: ChangeSet):
    # 1. Handle file movements (updates parent)
    for file_id, old_path, new_path in change_set.renamed_files:
        handle_file_move(file_id, old_path, new_path)
    
    # 2. Now safe to delete empty folder
    for folder_path in change_set.deleted_folders:
        folder_scope = scope_manager.get_scope_by_path(folder_path)
        if folder_scope:
            # Verify folder is empty
            children = scope_manager.get_children(folder_scope.id)
            if not children:
                delete_scope_tree(folder_scope.id)
            else:
                logger.warning(f"Folder {folder_path} not empty, skipping delete")
```

### Verification
- [ ] File move processed first
- [ ] File's new parent is correct
- [ ] Folder deletion doesn't orphan file
- [ ] No "dangling reference" errors

---

## Edge Case 5: Deeply Nested New File

### Scenario
```
DB state:
project/src/  (exists)

Disk state:
project/src/
    a/     (NEW)
        b/ (NEW)
            c/ (NEW)
                file.py (NEW)
```

### Problem
Current change detector might not detect `a/`, `b/`, `c/` if scanner doesn't traverse recursively.

### Detection Enhancement

**Fix in Scanner**:
```python
def _walk_folders(self) -> List[Path]:
    """Walk ALL folders recursively, not just top-level."""
    folders = []
    
    for root, dirs, files in os.walk(self.project_path):
        # Filter out ignored dirs
        dirs[:] = [d for d in dirs if d not in self.ignore_patterns]
        
        # Only include folders with Python files
        if any(f.endswith('.py') for f in files):
            folders.append(Path(root))
    
    return folders
```

**Fix in Change Detector**:
```python
def ensure_parent_folders_exist(new_file: str, new_folders: Set[str]):
    """Ensure all parent folders of a new file are in new_folders."""
    file_path = Path(new_file)
    
    # Walk up from file to project root
    for parent in file_path.parents:
        if parent == Path(self.project_path):
            break
        
        parent_str = str(parent)
        if parent_str not in db_folder_paths:
            new_folders.add(parent_str)
            logger.debug(f"Implicit new folder: {parent_str}")
```

### Solution

**Algorithm**:
1. Scanner returns ALL folders (recursive)
2. Change detector identifies missing parent folders
3. Collector processes folders depth-first (parent before child)

### Verification
- [ ] All intermediate folders detected
- [ ] Folders created in correct order (parent first)
- [ ] File has valid parent in graph

---

## Edge Case 6: Simultaneous Rename and Modify

### Scenario
```
Before:
src/old.py (ID: file-abc, checksum: "abc123")

After:
src/new.py (ID: file-abc, checksum: "def456")  # Renamed AND modified
```

### Detection
```python
# Scanner finds:
disk_files = {
    "file-abc": FileInfo(path="src/new.py", checksum="def456")
}

# Change detector logic:
if disk_path != db_path:
    # Renamed
    renamed_files.append(...)

if disk_checksum != db_checksum:
    # Modified
    modified_files.append(...)
```

**Result**: File appears in BOTH `renamed_files` AND `modified_files`

### Solution

**Approach**: Handle both changes

**Algorithm**:
```python
def process_renamed_and_modified(file_id: str, old_path: str, new_path: str):
    # Option 1: Two-step (preserve rename history)
    handle_file_rename(file_id, old_path, new_path)  # Update path
    sync_with_deletion(file_id, new_path)            # Re-parse content
    
    # Option 2: Simple (MVP)
    delete_scope_tree(file_id)   # Delete old
    reprocess_file(new_path)     # Create new with content
```

**Recommendation**: Use Option 2 for MVP (simpler, correct)

### Verification
- [ ] Path updated correctly
- [ ] Content changes reflected
- [ ] Call graph updated
- [ ] ID preserved (if using Option 1)

---

## Edge Case 7: Circular Folder Moves

### Scenario (Pathological)
```
This shouldn't happen in normal file systems, but just in case:

Before:
project/a/b/
project/c/

After:
project/c/a/b/
project/c/a/c/  # Wait, that's circular!
```

### Solution
**Detection**: Check for cycles during folder processing

**Code**:
```python
def detect_folder_cycle(folder_path: str, visited: Set[str]) -> bool:
    if folder_path in visited:
        logger.error(f"Cycle detected: {folder_path}")
        return True
    visited.add(folder_path)
    return False
```

**Mitigation**: Trust file system (OS prevents this), but log warning if detected

---

## Edge Case 8: File Rename During Sync

### Scenario
User renames a file while sync is in progress.

### Solution

**Approach**: Sync operates on a snapshot

**Algorithm**:
1. Scanner captures state at time T0
2. Sync processes based on snapshot
3. Next sync will see T1 state
4. No corruption because each sync is atomic

**Safety**: Don't modify files during sync (or warn user)

---

## Summary: Edge Case Handling Strategy

| Edge Case | Strategy | Priority |
|-----------|----------|----------|
| Folder rename with files | Recursive path update | High |
| File moved between folders | Update parent edge | High |
| Legacy file without ID | One-time ID assignment | High |
| Folder deleted, file moved | Process renames first | Medium |
| Deeply nested new files | Ensure parent folders | High |
| Rename + Modify | Delete-and-rebuild | Medium |
| Circular folder moves | Detect and log warning | Low |
| File changed during sync | Snapshot-based sync | Medium |

---

## Testing Recommendations

### For Each Edge Case
1. Write unit test with minimal example
2. Write integration test with real project
3. Verify DB state after change
4. Verify graph integrity (no orphans)
5. Verify reversibility (can undo)

### Regression Suite
- [ ] Test all 8 edge cases
- [ ] Combine multiple edge cases
- [ ] Test with large projects (1000+ files)
- [ ] Test concurrent changes (rapid renames)

---

## Next Steps
See [06_implementation_patterns.md](06_implementation_patterns.md) for reusable code patterns.
