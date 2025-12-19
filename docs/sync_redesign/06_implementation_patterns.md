# Implementation Patterns

This document provides reusable code patterns and utilities for implementing the ID-based sync system.

---

## Pattern 1: ID Extraction

### Extract ID from File

```python
import re
from pathlib import Path
from typing import Optional

def extract_id_from_file(file_path: Path) -> Optional[str]:
    """
    Extract module-level ID from file's first line comment.
    
    Expected format: # ID: a3f5b2c1-4d8e-9f1a-2b3c-4d5e6f7g8h9i
    
    Returns:
        UUID string if found, None otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read only first few lines for performance
            for _ in range(10):
                line = f.readline()
                if not line:
                    break
                
                match = re.match(r'^#\s*ID:\s*([a-f0-9\-]+)\s*$', line)
                if match:
                    return match.group(1)
        
        return None
    
    except (IOError, UnicodeDecodeError) as e:
        logger.warning(f"Failed to extract ID from {file_path}: {e}")
        return None
```

### Extract ID from Folder

```python
def extract_id_from_folder(folder_path: Path) -> Optional[str]:
    """
    Extract folder ID from __init__.py in the folder.
    
    Expected format: # Folder ID: b4g6c3d2-5e9f-0g2b-3c4d-5e6f7g8h9i0j
    
    Returns:
        UUID string if found, None otherwise
    """
    init_file = folder_path / '__init__.py'
    
    if not init_file.exists():
        return None
    
    try:
        content = init_file.read_text(encoding='utf-8')
        match = re.search(
            r'^#\s*Folder ID:\s*([a-f0-9\-]+)\s*$',
            content,
            re.MULTILINE
        )
        return match.group(1) if match else None
    
    except (IOError, UnicodeDecodeError) as e:
        logger.warning(f"Failed to extract folder ID from {init_file}: {e}")
        return None
```

### Validate UUID Format

```python
import uuid

def is_valid_uuid(uuid_str: str) -> bool:
    """
    Validate that a string is a properly formatted UUID.
    
    Returns:
        True if valid UUID, False otherwise
    """
    try:
        uuid.UUID(uuid_str)
        return True
    except (ValueError, AttributeError):
        return False
```

---

## Pattern 2: ID Injection

### Inject ID into Module

```python
def inject_module_id(content: str, module_id: Optional[str] = None) -> str:
    """
    Inject module-level ID as first line comment.
    If ID already exists, returns content unchanged.
    
    Args:
        content: File content
        module_id: ID to inject (generates new UUID if None)
    
    Returns:
        Modified content with ID
    """
    # Check if ID already exists
    first_line = content.split('\n')[0] if content else ""
    if re.match(r'^#\s*ID:', first_line):
        return content  # Already has ID
    
    # Generate or use provided ID
    if module_id is None:
        module_id = str(uuid.uuid4())
    
    # Inject as first line
    id_comment = f"# ID: {module_id}\n"
    return id_comment + content
```

### Inject ID into Folder

```python
def inject_folder_id(folder_path: Path, folder_id: Optional[str] = None) -> str:
    """
    Ensure __init__.py exists with folder ID.
    
    Args:
        folder_path: Path to folder
        folder_id: ID to inject (generates new UUID if None)
    
    Returns:
        The folder ID (existing or newly created)
    """
    init_file = folder_path / '__init__.py'
    
    # Check for existing ID
    existing_id = extract_id_from_folder(folder_path)
    if existing_id:
        return existing_id
    
    # Generate or use provided ID
    if folder_id is None:
        folder_id = str(uuid.uuid4())
    
    # Prepare content
    id_comment = f"# Folder ID: {folder_id}\n"
    
    if init_file.exists():
        # Prepend to existing content
        existing_content = init_file.read_text(encoding='utf-8')
        new_content = id_comment + "\n" + existing_content
    else:
        # Create new file
        new_content = id_comment
    
    # Write file
    init_file.write_text(new_content, encoding='utf-8')
    
    return folder_id
```

---

## Pattern 3: Scope Deletion

### Delete Scope Tree (Recursive)

```python
from typing import List

def delete_scope_tree(scope_id: str, scope_manager: ScopeManager):
    """
    Delete a scope and all its descendants from the database.
    
    Order:
    1. Delete call sites for all scopes
    2. Delete scopes bottom-up (children before parents)
    
    Args:
        scope_id: Root scope to delete
        scope_manager: ScopeManager instance
    """
    # 1. Get all descendants (DFS, post-order)
    descendants = _get_descendants_post_order(scope_id, scope_manager)
    
    # 2. Delete call sites (prevents orphan CallNodes)
    all_scopes = descendants + [scope_id]
    for sid in all_scopes:
        scope_manager.delete_call_sites(sid)
        logger.debug(f"Deleted call sites for scope {sid}")
    
    # 3. Delete scopes (bottom-up, so children deleted before parents)
    for sid in descendants:
        scope_manager.delete_scope(sid)
        logger.debug(f"Deleted scope {sid}")
    
    # 4. Delete root scope
    scope_manager.delete_scope(scope_id)
    logger.info(f"Deleted scope tree rooted at {scope_id}")


def _get_descendants_post_order(scope_id: str, scope_manager: ScopeManager) -> List[str]:
    """
    Get all descendant scope IDs in post-order (children before parents).
    
    Returns:
        List of scope IDs, with deepest descendants first
    """
    result = []
    
    def traverse(sid: str):
        children = scope_manager.get_children(sid)
        for child in children:
            traverse(child.id)  # Recurse first
        result.append(sid)    # Then add current
    
    # Start traversal (but don't include root in result)
    children = scope_manager.get_children(scope_id)
    for child in children:
        traverse(child.id)
    
    return result
```

### Delete with Verification

```python
def delete_scope_tree_safe(scope_id: str, scope_manager: ScopeManager) -> bool:
    """
    Delete scope tree with verification that it's safe.
    
    Checks:
    - Scope exists
    - No external references (optional, for safety)
    
    Returns:
        True if deleted successfully, False otherwise
    """
    # Verify scope exists
    scope = scope_manager.get_scope(scope_id)
    if not scope:
        logger.warning(f"Scope {scope_id} not found, skipping delete")
        return False
    
    # Get count of descendants for logging
    descendants = _get_descendants_post_order(scope_id, scope_manager)
    total_count = len(descendants) + 1
    
    logger.info(f"Deleting scope tree: {scope_id} ({total_count} total scopes)")
    
    # Perform deletion
    try:
        delete_scope_tree(scope_id, scope_manager)
        return True
    except Exception as e:
        logger.error(f"Failed to delete scope tree {scope_id}: {e}")
        return False
```

---

## Pattern 4: QName Updates

### Update QName on Rename

```python
def update_qname_on_rename(
    scope_id: str,
    old_path: str,
    new_path: str,
    scope_manager: ScopeManager
):
    """
    Update qname for a scope and all descendants when path changes.
    
    Args:
        scope_id: Scope to update
        old_path: Previous file/folder path
        new_path: New file/folder path
        scope_manager: ScopeManager instance
    """
    # Convert paths to qnames
    old_qname_prefix = path_to_qname(old_path)
    new_qname_prefix = path_to_qname(new_path)
    
    # Update current scope
    scope = scope_manager.get_scope(scope_id)
    scope.qname = scope.qname.replace(old_qname_prefix, new_qname_prefix, 1)
    scope.file_path = new_path
    scope_manager.update_scope(scope)
    
    logger.debug(f"Updated scope {scope_id}: qname={scope.qname}, path={new_path}")
    
    # Recursively update descendants
    _update_descendants_qname(scope_id, old_qname_prefix, new_qname_prefix, scope_manager)


def _update_descendants_qname(
    parent_id: str,
    old_prefix: str,
    new_prefix: str,
    scope_manager: ScopeManager
):
    """Recursively update qnames of all descendants."""
    children = scope_manager.get_children(parent_id)
    
    for child in children:
        # Update child's qname
        child.qname = child.qname.replace(old_prefix, new_prefix, 1)
        scope_manager.update_scope(child)
        
        # Recurse for nested children
        _update_descendants_qname(child.id, old_prefix, new_prefix, scope_manager)
```

### Path to QName Conversion

```python
def path_to_qname(file_path: str, project_root: Optional[Path] = None) -> str:
    """
    Convert file path to qualified name.
    
    Examples:
        src/main.py → src.main
        src/package/__init__.py → src.package
        src/package/module.py → src.package.module
    
    Args:
        file_path: Relative path from project root
        project_root: Optional project root (for making path relative)
    
    Returns:
        Qualified name (dotted notation)
    """
    path = Path(file_path)
    
    # Make relative to project root if provided
    if project_root:
        path = path.relative_to(project_root)
    
    # Remove .py extension
    if path.suffix == '.py':
        path = path.with_suffix('')
    
    # Handle __init__.py (package marker)
    if path.name == '__init__':
        path = path.parent
    
    # Convert path separators to dots
    qname = '.'.join(path.parts)
    
    return qname
```

---

## Pattern 5: Parent Folder Lookup

### Get Parent Folder Scope

```python
def get_parent_folder_scope(
    file_path: str,
    scope_manager: ScopeManager
) -> Optional[ScopeModel]:
    """
    Get the parent folder scope for a file.
    
    Args:
        file_path: Path to file
        scope_manager: ScopeManager instance
    
    Returns:
        Parent folder scope, or None if not found
    """
    folder_path = str(Path(file_path).parent)
    
    # Try to find folder scope by path
    folder_scope = scope_manager.get_scope_by_path(folder_path)
    
    if not folder_scope:
        logger.warning(f"Parent folder not found for {file_path}")
    
    return folder_scope
```

### Ensure Parent Exists

```python
def ensure_parent_folder_exists(
    file_path: str,
    scope_manager: ScopeManager,
    collector: Collector
) -> ScopeModel:
    """
    Ensure parent folder scope exists, creating if necessary.
    
    Args:
        file_path: Path to file
        scope_manager: ScopeManager instance
        collector: Collector instance for creating folders
    
    Returns:
        Parent folder scope
    """
    parent_scope = get_parent_folder_scope(file_path, scope_manager)
    
    if parent_scope:
        return parent_scope
    
    # Parent doesn't exist, create it
    folder_path = Path(file_path).parent
    
    logger.info(f"Creating missing parent folder: {folder_path}")
    
    # Process folder (will recursively ensure grandparents exist too)
    folder_results = collector.process_folder(folder_path)
    
    # Return the immediate parent
    return scope_manager.get_scope_by_path(str(folder_path))
```

---

## Pattern 6: Checksum Computation

### Compute File Checksum

```python
import hashlib

def compute_checksum(file_path: Path, algorithm: str = 'md5') -> str:
    """
    Compute checksum of file content.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm ('md5', 'sha256', etc.)
    
    Returns:
        Hex digest of file content
    """
    hash_obj = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            # Read in chunks for memory efficiency
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    except IOError as e:
        logger.error(f"Failed to compute checksum for {file_path}: {e}")
        return ""
```

### Fast Checksum (Metadata-Based)

```python
import os

def compute_fast_checksum(file_path: Path) -> str:
    """
    Compute fast checksum using file metadata (size + mtime).
    
    Faster than content hash, but less accurate (doesn't detect touch/rewrite).
    
    Returns:
        Checksum string
    """
    try:
        stat = os.stat(file_path)
        return f"{stat.st_size}_{stat.st_mtime_ns}"
    except OSError as e:
        logger.error(f"Failed to stat {file_path}: {e}")
        return ""
```

---

## Pattern 7: Batch Operations

### Batch Update Scopes

```python
def batch_update_scopes(
    updates: List[Tuple[str, dict]],
    scope_manager: ScopeManager
):
    """
    Update multiple scopes in a batch.
    
    Args:
        updates: List of (scope_id, updates_dict) tuples
        scope_manager: ScopeManager instance
    
    Example:
        batch_update_scopes([
            ("scope-1", {"qname": "new.qname"}),
            ("scope-2", {"file_path": "new/path.py"})
        ], scope_manager)
    """
    logger.info(f"Batch updating {len(updates)} scopes")
    
    for scope_id, update_dict in updates:
        scope = scope_manager.get_scope(scope_id)
        if not scope:
            logger.warning(f"Scope {scope_id} not found, skipping")
            continue
        
        # Apply updates
        for key, value in update_dict.items():
            setattr(scope, key, value)
        
        scope_manager.update_scope(scope)
    
    logger.info(f"Batch update complete")
```

---

## Pattern 8: Error Handling

### Retry with Backoff

```python
import time
from typing import Callable, TypeVar

T = TypeVar('T')

def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = 3,
    initial_delay: float = 0.1
) -> T:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
    
    Returns:
        Result of func()
    
    Raises:
        Last exception if all retries fail
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            
            if attempt < max_retries:
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                logger.error(f"All {max_retries + 1} attempts failed")
    
    raise last_exception
```

---

## Utilities Module Template

Create `src/backend/app/core/parser/graph_builder/utils/id_utils.py`:

```python
"""Utility functions for ID-based sync system."""

import re
import uuid
import hashlib
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# ID Extraction
def extract_id_from_file(file_path: Path) -> Optional[str]:
    # ... (implementation from Pattern 1)

def extract_id_from_folder(folder_path: Path) -> Optional[str]:
    # ... (implementation from Pattern 1)

def is_valid_uuid(uuid_str: str) -> bool:
    # ... (implementation from Pattern 1)

# ID Injection
def inject_module_id(content: str, module_id: Optional[str] = None) -> str:
    # ... (implementation from Pattern 2)

def inject_folder_id(folder_path: Path, folder_id: Optional[str] = None) -> str:
    # ... (implementation from Pattern 2)

# Path Utilities
def path_to_qname(file_path: str, project_root: Optional[Path] = None) -> str:
    # ... (implementation from Pattern 4)

# Checksum
def compute_checksum(file_path: Path, algorithm: str = 'md5') -> str:
    # ... (implementation from Pattern 6)
```

---

## Summary

These patterns provide:
- ✅ Robust ID extraction and injection
- ✅ Safe scope deletion (bottom-up)
- ✅ QName updates on renames
- ✅ Parent folder management
- ✅ Efficient checksumming
- ✅ Batch operations
- ✅ Error handling

Use these as building blocks for the migration plan implementation.
