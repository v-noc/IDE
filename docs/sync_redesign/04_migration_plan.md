# Migration Plan

## Overview

This document provides a step-by-step plan to migrate from the current path-based sync system to the new ID-based system. The migration is broken into 5 phases, each with clear deliverables and testing requirements.

---

## Phase 1: ID Injection Infrastructure

**Goal**: Ensure every file and folder has a persistent ID stored on disk.

### Step 1.1: Extend `id_injector.py` for Module-Level IDs

**Location**: `src/backend/app/core/parser/ast/id_injector.py`

**Current Functionality**: Injects IDs into function and class docstrings

**New Requirement**: Add module-level ID as a comment at the top of the file

#### Implementation

- [ ] Add `leave_Module` method to `IDInjector` class
- [ ] Extract existing `# ID:` comment if present
- [ ] Generate and inject new UUID if missing
- [ ] Mark as modified if injection occurred

**Code Changes**:
```python
def leave_Module(
    self,
    original_node: cst.Module,
    updated_node: cst.Module
) -> cst.Module:
    """Add module-level ID comment as first line if missing."""
    
    # Check if first statement is an ID comment
    if updated_node.header:
        for line in updated_node.header:
            if isinstance(line, cst.EmptyLine) and line.comment:
                if line.comment.value.startswith("# ID:"):
                    return updated_node  # ID exists
    
    # No ID found, inject one
    self.modified = True
    new_id = str(uuid4())
    id_line = cst.EmptyLine(
        comment=cst.Comment(f"# ID: {new_id}"),
        newline=cst.Newline()
    )
    
    new_header = (id_line,) + (updated_node.header or ())
    return updated_node.with_changes(header=new_header)
```

#### Testing
- [ ] Unit test: File with no ID → ID is injected
- [ ] Unit test: File with existing ID → No modification
- [ ] Unit test: Verify ID format (valid UUID)
- [ ] Unit test: ID is first line in file

### Step 1.2: Create Folder ID Manager

**Location**: Create new file `src/backend/app/core/parser/ast/folder_id_manager.py`

**Purpose**: Manage IDs stored in `__init__.py` files for folders

#### Implementation

- [ ] Create `FolderIDManager` class
- [ ] Implement `get_or_create_folder_id(folder_path: Path) -> str`
- [ ] Implement `extract_id_from_init(init_path: Path) -> Optional[str]`
- [ ] Implement `write_id_to_init(init_path: Path, folder_id: str)`

**Code Structure**:
```python
class FolderIDManager:
    @staticmethod
    def get_or_create_folder_id(folder_path: Path) -> str:
        """Get existing folder ID or create new one."""
        pass
    
    @staticmethod
    def extract_id_from_init(init_path: Path) -> Optional[str]:
        """Extract folder ID from __init__.py."""
        pass
    
    @staticmethod
    def write_id_to_init(init_path: Path, folder_id: str):
        """Write folder ID to __init__.py."""
        pass
```

#### Testing
- [ ] Unit test: Empty folder → Creates `__init__.py` with ID
- [ ] Unit test: Existing `__init__.py` without ID → Adds ID
- [ ] Unit test: Existing `__init__.py` with ID → Returns existing ID
- [ ] Unit test: Non-existent folder → Raises appropriate error
- [ ] Unit test: Read-only folder → Handles permission error gracefully

### Step 1.3: Migration Script for Existing Projects

**Location**: Create `src/backend/scripts/assign_ids_to_project.py`

**Purpose**: One-time script to inject IDs into existing codebases

#### Implementation

- [ ] Create CLI script that takes project path
- [ ] Walk all `.py` files
- [ ] Inject module-level IDs using `inject_ids()`
- [ ] Walk all folders with Python files
- [ ] Ensure folder IDs using `FolderIDManager`
- [ ] Log progress and summary

**Script Structure**:
```python
def assign_ids_to_project(project_path: Path, dry_run: bool = False):
    """Inject IDs into all files and folders in project."""
    files_modified = 0
    folders_modified = 0
    
    # Process files
    for py_file in project_path.rglob('*.py'):
        if '__pycache__' in py_file.parts:
            continue
        
        content = py_file.read_text()
        new_content, modified = inject_ids(content)
        
        if modified:
            if not dry_run:
                py_file.write_text(new_content)
            files_modified += 1
            logger.info(f"Added ID to {py_file}")
    
    # Process folders
    for folder in project_path.rglob('*/'):
        if folder.name == '__pycache__':
            continue
        
        # Only process Python package folders
        if any(folder.glob('*.py')):
            folder_id = FolderIDManager.get_or_create_folder_id(folder)
            folders_modified += 1
            logger.info(f"Ensured ID for {folder}: {folder_id}")
    
    return files_modified, folders_modified
```

#### Testing
- [ ] Integration test: Run on sample project
- [ ] Verify all files have IDs
- [ ] Verify all folders with Python files have IDs
- [ ] Test dry-run mode (no actual writes)
- [ ] Test idempotence (run twice, second run changes nothing)

---

## Phase 2: Scanner Integration

**Goal**: Update scanner to extract IDs during file system scan.

### Step 2.1: Update Scanner Data Models

**Location**: `src/backend/app/core/parser/graph_builder/discovery/scanner.py`

#### Implementation

- [ ] Define `FileInfo` dataclass with `path`, `id`, `checksum`
- [ ] Define `FolderInfo` dataclass with `path`, `id`
- [ ] Update `ScanResult` to use new dataclasses

**Code Changes**:
```python
@dataclass
class FileInfo:
    path: str
    id: Optional[str]
    checksum: str

@dataclass
class FolderInfo:
    path: str
    id: Optional[str]

@dataclass
class ScanResult:
    files: Dict[str, FileInfo]      # path → FileInfo
    folders: Dict[str, FolderInfo]  # path → FolderInfo
```

### Step 2.2: Update Scanner Logic

**Location**: `scanner.py:FileScanner.scan()`

#### Implementation

- [ ] Extract file ID when scanning each file
- [ ] Extract folder ID when scanning each folder
- [ ] Handle missing IDs gracefully (log warning)

**Code Changes**:
```python
def scan(self) -> ScanResult:
    files = {}
    folders = {}
    
    for file_path in self._walk_python_files():
        file_id = self._extract_file_id(file_path)
        checksum = self._compute_checksum(file_path)
        
        files[str(file_path)] = FileInfo(
            path=str(file_path),
            id=file_id,
            checksum=checksum
        )
    
    for folder_path in self._walk_folders():
        folder_id = FolderIDManager.get_or_create_folder_id(folder_path)
        
        folders[str(folder_path)] = FolderInfo(
            path=str(folder_path),
            id=folder_id
        )
    
    return ScanResult(files=files, folders=folders)

def _extract_file_id(self, file_path: Path) -> Optional[str]:
    """Extract ID from file's first line comment."""
    try:
        content = file_path.read_text()
        match = re.search(r'^# ID:\s*([a-f0-9\-]+)', content, re.MULTILINE)
        return match.group(1) if match else None
    except Exception as e:
        logger.warning(f"Failed to extract ID from {file_path}: {e}")
        return None
```

#### Testing
- [ ] Unit test: Scan file with ID → ID is extracted
- [ ] Unit test: Scan file without ID → Returns None
- [ ] Unit test: Scan folder with ID in `__init__.py` → ID is extracted
- [ ] Integration test: Scan real project → All IDs populated

---

## Phase 3: ID-Based Change Detection

**Goal**: Detect changes using IDs instead of paths, enabling rename detection.

### Step 3.1: Update ChangeSet Data Model

**Location**: `src/backend/app/core/parser/graph_builder/discovery/change_detector.py`

#### Implementation

- [ ] Add `renamed_files: List[Tuple[str, str, str]]` to `ChangeSet` (id, old_path, new_path)
- [ ] Add `renamed_folders: List[Tuple[str, str, str]]` to `ChangeSet`

**Code Changes**:
```python
@dataclass
class ChangeSet:
    new_files: List[str]
    modified_files: List[str]
    deleted_files: List[str]
    renamed_files: List[Tuple[str, str, str]]  # NEW: (id, old_path, new_path)
    new_folders: List[str]
    deleted_folders: List[str]
    renamed_folders: List[Tuple[str, str, str]]  # NEW: (id, old_path, new_path)
```

### Step 3.2: Implement ID-Based Change Detection

**Location**: `change_detector.py:ChangeDetector.detect_changes()`

#### Implementation

- [ ] Build `disk_files_by_id` mapping
- [ ] Build `db_files_by_id` mapping from scope manager
- [ ] Compare by ID to detect renames
- [ ] Fall back to path-based detection for files without IDs

**Code Changes**:
```python
def detect_changes(self, scan_result: ScanResult) -> ChangeSet:
    # ID-based detection for files
    disk_files_by_id = {
        fi.id: fi for fi in scan_result.files.values() if fi.id
    }
    
    db_scopes = self.manager.get_all_file_scopes()
    db_files_by_id = {
        scope.id: scope for scope in db_scopes if scope.id
    }
    
    renamed_files = []
    
    # Detect renames
    for file_id in set(disk_files_by_id.keys()) & set(db_files_by_id.keys()):
        disk_info = disk_files_by_id[file_id]
        db_scope = db_files_by_id[file_id]
        
        if disk_info.path != db_scope.file_path:
            renamed_files.append((file_id, db_scope.file_path, disk_info.path))
    
    # ... rest of change detection logic
```

#### Testing
- [ ] Unit test: File renamed → Detected as rename, not delete+create
- [ ] Unit test: File modified (same path) → Detected as modified
- [ ] Unit test: File moved to different folder → Detected as rename
- [ ] Unit test: Folder renamed → Detected in renamed_folders
- [ ] Integration test: Complex scenario with multiple rename types

---

## Phase 4: Update Sync Logic

**Goal**: Implement delete-and-rebuild and smart rename handling.

### Step 4.1: Implement Delete-and-Rebuild

**Location**: Create `src/backend/app/core/parser/graph_builder/sync/deletion_service.py`

#### Implementation

- [ ] Create `DeletionService` class
- [ ] Implement `delete_scope_tree(scope_id: str)` method
- [ ] Get all descendants via scope manager
- [ ] Delete call sites for each scope
- [ ] Delete scopes bottom-up

**Code Structure**:
```python
class DeletionService:
    def delete_scope_tree(self, scope_id: str):
        """Delete scope and all descendants from DB."""
        descendants = self.scope_manager.get_descendants(scope_id)
        
        # Delete call sites
        for scope in descendants + [scope_id]:
            self.scope_manager.delete_call_sites(scope)
        
        # Delete scopes (bottom-up)
        for scope in reversed(descendants):
            self.scope_manager.delete_scope(scope)
        
        self.scope_manager.delete_scope(scope_id)
```

#### Testing
- [ ] Unit test: Delete file scope → All child scopes deleted
- [ ] Unit test: Delete folder scope → Entire subtree deleted
- [ ] Unit test: Verify call sites are cleaned up
- [ ] Integration test: Delete and verify DB state

### Step 4.2: Implement Smart Rename Handling

**Location**: `src/backend/app/core/parser/graph_builder/sync/rename_service.py`

#### Implementation

- [ ] Create `RenameService` class
- [ ] Implement `handle_file_rename(scope_id, old_path, new_path)`
- [ ] Update scope's `file_path` and `qname`
- [ ] Recursively update all descendant scopes

**Code Structure**:
```python
class RenameService:
    def handle_file_rename(self, scope_id: str, old_path: str, new_path: str):
        """Update file path and qname without deleting."""
        scope = self.scope_manager.get_scope(scope_id)
        
        # Update scope
        scope.file_path = new_path
        scope.qname = self._path_to_qname(new_path)
        self.scope_manager.update_scope(scope)
        
        # Update children
        self._update_children_qname(scope_id, old_path, new_path)
```

#### Testing
- [ ] Unit test: Rename file → Path and qname updated
- [ ] Unit test: Rename preserves ID
- [ ] Unit test: Children qnames updated correctly
- [ ] Integration test: Rename + verify call graph intact

### Step 4.3: Remove Version Filtering from Queries

**Location**: `src/backend/app/core/repository/base/node_repo.py`

#### Implementation

- [ ] Locate all AQL queries with version filtering
- [ ] Remove `PRUNE` clauses that check `current_version`
- [ ] Optionally keep `current_version` field for audit

**Code Changes**:
```python
# Before
FOR v, e, p IN 1..@max_depth OUTBOUND @start contains_edges
    PRUNE (v.current_version < parent.current_version)
    RETURN v

# After
FOR v, e, p IN 1..@max_depth OUTBOUND @start contains_edges
    RETURN v
```

#### Testing
- [ ] Unit test: Query returns full tree (no pruning)
- [ ] Performance test: Measure query time on large tree
- [ ] Integration test: Verify correctness with nested structures

---

## Phase 5: Orchestrator Integration

**Goal**: Wire up all components in the orchestrator.

### Step 5.1: Update Orchestrator Change Processing

**Location**: `src/backend/app/core/parser/graph_builder/orchestrator.py:_process_changes()`

#### Implementation

- [ ] Handle renamed files using `RenameService`
- [ ] Handle modified/new files using delete-and-rebuild
- [ ] Handle deleted files using `DeletionService`

**Code Changes**:
```python
def _process_changes(self, change_set: ChangeSet):
    # 1. Handle pure renames (no content change)
    for scope_id, old_path, new_path in change_set.renamed_files:
        if self._is_pure_rename(old_path, new_path, change_set):
            self.rename_service.handle_file_rename(scope_id, old_path, new_path)
    
    # 2. Handle modified files (delete and rebuild)
    for file_path in change_set.modified_files:
        scope = self.scope_manager.get_scope_by_path(file_path)
        if scope:
            self.deletion_service.delete_scope_tree(scope.id)
        # Re-collect and sync
        self.collector.process_file(file_path)
    
    # 3. Handle new files
    for file_path in change_set.new_files:
        self.collector.process_file(file_path)
    
    # 4. Handle deletions
    for file_path in change_set.deleted_files:
        scope = self.scope_manager.get_scope_by_path(file_path)
        if scope:
            self.deletion_service.delete_scope_tree(scope.id)
```

#### Testing
- [ ] Integration test: Full resync with renames
- [ ] Integration test: Mixed changes (new, modified, deleted, renamed)
- [ ] Integration test: Nested folder renames
- [ ] Performance test: Large project resync

---

## Testing Strategy

### Unit Tests
- ID injection (Phase 1)
- Folder ID management (Phase 1)
- Scanner ID extraction (Phase 2)
- Change detection by ID (Phase 3)
- Deletion service (Phase 4)
- Rename service (Phase 4)

### Integration Tests
- End-to-end resync with ID-based system
- Rename scenarios (file, folder, nested)
- Mixed change scenarios
- Legacy project migration

### Performance Tests
- Sync time for projects of various sizes
- Query performance without version filtering
- Memory usage during large syncs

---

## Rollout Plan

### Week 1: Foundation
- Complete Phase 1 (ID injection infrastructure)
- Run migration script on test projects
- Verify all files have IDs

### Week 2: Detection
- Complete Phase 2 (Scanner integration)
- Complete Phase 3 (Change detection)
- Test rename detection with sample projects

### Week 3: Sync Logic
- Complete Phase 4 (Sync strategies)
- Implement delete-and-rebuild
- Implement smart rename handling

### Week 4: Integration & Testing
- Complete Phase 5 (Orchestrator)
- Run full integration tests
- Performance tuning

### Week 5: Production Migration
- Run ID migration on production projects
- Monitor first sync
- Iterate on issues

---

## Rollback Strategy

If issues arise:

1. **Phase 1-2**: Safe to rollback (only added IDs to files)
2. **Phase 3-5**: Revert code changes, use old sync logic
3. **IDs on disk**: Keep them (harmless comments, useful for future)

---

## Success Criteria

- [ ] All files tracked by ID
- [ ] All folders tracked by ID
- [ ] Renames detected correctly (no delete+create)
- [ ] Sync completes successfully on test projects
- [ ] No performance regression on large projects
- [ ] All existing tests pass
- [ ] New tests pass (unit + integration)

---

## Next Steps

See [05_edge_cases.md](05_edge_cases.md) for detailed edge case handling.
