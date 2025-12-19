# ID-Based Tracking Solution

## Core Concept

**Replace path-based identity with persistent IDs.**

### Current Approach
```python
# Identity tied to path
FileModel(
    qname="src.main",
    file_path="src/main.py"
)

# Problem: Rename changes identity
# src/main.py → src/renamed.py
# Result: Delete + Create new
```

### New Approach
```python
# Identity tied to persistent ID
FileModel(
    id="a3f5b2c1-4d8e-9f1a-2b3c-4d5e6f7g8h9i",
    qname="src.main",
    file_path="src/main.py"
)

# Benefit: Rename detected and handled
# src/main.py → src/renamed.py
# Result: Update path, preserve ID and children
```

## ID Storage Mechanism

### For Files

**Approach**: Inject ID as a comment at the top of the file

**Example**:
```python
# ID: a3f5b2c1-4d8e-9f1a-2b3c-4d5e6f7g8h9i

"""Module docstring."""

def my_function():
    pass
```

**Implementation Location**: Extend existing `src/backend/app/core/parser/ast/id_injector.py`

**Current Status**: Already implements ID injection for functions and classes via docstrings

**New Requirement**: Add module-level ID injection

#### Proposed Implementation

```python
class IDInjector(cst.CSTTransformer):
    def __init__(self):
        self.modified = False
        self.module_id = None  # NEW
    
    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        """Add module-level ID comment as first line."""
        # Extract existing ID comment if present
        first_line = updated_node.body[0] if updated_node.body else None
        
        if isinstance(first_line, cst.EmptyLine):
            comment = first_line.comment
            if comment and comment.value.startswith("# ID:"):
                # ID already exists
                return updated_node
        
        # No ID found, inject one
        self.modified = True
        new_id = str(uuid4())
        id_comment = cst.EmptyLine(
            comment=cst.Comment(f"# ID: {new_id}")
        )
        
        new_body = (id_comment,) + updated_node.body
        return updated_node.with_changes(body=new_body)
```

### For Folders

**Approach**: Store ID in `__init__.py` file within the folder

**Example**:
```python
# Folder ID: b4g6c3d2-5e9f-0g2b-3c4d-5e6f7g8h9i0j

"""Package initialization."""

# Rest of __init__.py content
```

**Rationale**:
- Folders don't have content themselves (unlike files)
- `__init__.py` is a standard Python convention
- If `__init__.py` doesn't exist, we create it (common practice)

#### Proposed Implementation

Create a new module: `src/backend/app/core/parser/ast/folder_id_manager.py`

```python
from pathlib import Path
from uuid import uuid4
import re
from typing import Optional

class FolderIDManager:
    @staticmethod
    def get_or_create_folder_id(folder_path: Path) -> str:
        """Get existing folder ID or create new one."""
        init_file = folder_path / '__init__.py'
        
        # Try to read existing ID
        if init_file.exists():
            content = init_file.read_text()
            match = re.search(
                r'^# Folder ID:\s*([a-f0-9\-]+)',
                content,
                re.MULTILINE
            )
            if match:
                return match.group(1)
        
        # No ID found, create one
        new_id = str(uuid4())
        FolderIDManager._write_id_to_init(init_file, new_id)
        return new_id
    
    @staticmethod
    def _write_id_to_init(init_file: Path, folder_id: str):
        """Write/update folder ID in __init__.py."""
        if init_file.exists():
            content = init_file.read_text()
            # Remove existing ID if present
            content = re.sub(
                r'^# Folder ID:\s*[a-f0-9\-]+\n?',
                '',
                content,
                flags=re.MULTILINE
            )
            new_content = f"# Folder ID: {folder_id}\n\n{content}".lstrip()
        else:
            new_content = f"# Folder ID: {folder_id}\n"
        
        init_file.write_text(new_content)
```

## ID-Based Change Detection

### New Algorithm

**Location**: Update `src/backend/app/core/parser/graph_builder/discovery/change_detector.py`

```python
from typing import Dict, Tuple
from dataclasses import dataclass

@dataclass
class FileInfo:
    path: str
    id: str
    checksum: str

@dataclass
class ChangeSet:
    new_files: List[str]
    modified_files: List[str]
    deleted_files: List[str]
    renamed_files: List[Tuple[str, str, str]]  # (id, old_path, new_path)
    new_folders: List[str]
    deleted_folders: List[str]
    renamed_folders: List[Tuple[str, str, str]]  # (id, old_path, new_path)

class ChangeDetector:
    def detect_changes_with_ids(self, scan_result: ScanResult) -> ChangeSet:
        # 1. Build ID → FileInfo mappings from disk
        disk_files_by_id: Dict[str, FileInfo] = {}
        
        for path, file_info in scan_result.files.items():
            if file_info.id:  # Only if ID was extracted
                disk_files_by_id[file_info.id] = file_info
        
        # 2. Build ID → ScopeModel mappings from DB
        db_scopes = self.manager.get_all_file_scopes()
        db_files_by_id: Dict[str, ScopeModel] = {
            scope.id: scope for scope in db_scopes
        }
        
        # 3. Detect changes by ID
        new_files = []
        modified_files = []
        deleted_files = []
        renamed_files = []
        
        all_ids = set(disk_files_by_id.keys()) | set(db_files_by_id.keys())
        
        for file_id in all_ids:
            disk_info = disk_files_by_id.get(file_id)
            db_scope = db_files_by_id.get(file_id)
            
            if disk_info and not db_scope:
                # New file (ID not in DB)
                new_files.append(disk_info.path)
            
            elif db_scope and not disk_info:
                # Deleted file (ID no longer on disk)
                deleted_files.append(db_scope.file_path)
            
            elif disk_info and db_scope:
                # File exists in both
                if disk_info.path != db_scope.file_path:
                    # Path changed → Rename detected!
                    renamed_files.append((
                        file_id,
                        db_scope.file_path,
                        disk_info.path
                    ))
                
                elif disk_info.checksum != db_scope.checksum:
                    # Content changed
                    modified_files.append(disk_info.path)
        
        # Same logic for folders...
        
        return ChangeSet(
            new_files=new_files,
            modified_files=modified_files,
            deleted_files=deleted_files,
            renamed_files=renamed_files,
            # ... folders
        )
```

### Key Benefits

| Scenario | Old Behavior | New Behavior |
|----------|-------------|--------------|
| **File Rename** | Delete + Create | Update path, preserve ID |
| **Folder Rename** | Delete subtree + Recreate | Update paths recursively |
| **File Move** | Delete + Create | Update path + parent edge |
| **Content Change** | Detected by checksum | Same (still use checksum) |

## Scanner Integration

### Update Scanner Output

**Location**: `src/backend/app/core/parser/graph_builder/discovery/scanner.py`

**Current**:
```python
@dataclass
class ScanResult:
    files: Dict[str, str]  # path → checksum
    folders: List[str]     # paths
```

**New**:
```python
@dataclass
class FileInfo:
    path: str
    id: Optional[str]  # Extracted from file
    checksum: str

@dataclass
class FolderInfo:
    path: str
    id: Optional[str]  # Extracted from __init__.py

@dataclass
class ScanResult:
    files: Dict[str, FileInfo]      # path → FileInfo
    folders: Dict[str, FolderInfo]  # path → FolderInfo
```

### Scanner Implementation

```python
def scan(self) -> ScanResult:
    files = {}
    folders = {}
    
    for file_path in self._walk_files():
        file_id = extract_id_from_file(file_path)
        checksum = compute_checksum(file_path)
        files[str(file_path)] = FileInfo(
            path=str(file_path),
            id=file_id,
            checksum=checksum
        )
    
    for folder_path in self._walk_folders():
        folder_id = extract_id_from_folder(folder_path)
        folders[str(folder_path)] = FolderInfo(
            path=str(folder_path),
            id=folder_id
        )
    
    return ScanResult(files=files, folders=folders)
```

## Migration Strategy for Existing Files

### Challenge
Existing files in the codebase don't have IDs yet.

### Solution: One-Time ID Assignment

```python
def assign_ids_to_project(project_path: Path):
    """One-time migration: Inject IDs into all files/folders."""
    
    # 1. Walk all Python files
    for py_file in project_path.rglob('*.py'):
        content = py_file.read_text()
        new_content, modified = inject_ids(content)
        
        if modified:
            py_file.write_text(new_content)
            print(f"Added ID to {py_file}")
    
    # 2. Walk all folders
    for folder in project_path.rglob('*/'):
        if folder.name == '__pycache__':
            continue
        
        folder_id = FolderIDManager.get_or_create_folder_id(folder)
        print(f"Ensured ID for folder {folder}: {folder_id}")
```

**When to run**: 
- Before first sync with new system
- Can be run multiple times (idempotent)

## Summary

### What Changes
✅ Files get `# ID: <uuid>` as first line
✅ Folders get `# Folder ID: <uuid>` in `__init__.py`
✅ Scanner extracts IDs during scan
✅ Change detector uses IDs as primary key
✅ Renames are detected as renames, not delete+create

### What Stays the Same
✅ Checksum-based modification detection
✅ ScopeManager structure
✅ Graph database schema (just use existing `id` field)

### Next Steps
See [03_sync_strategies.md](03_sync_strategies.md) for how to handle the detected changes.
