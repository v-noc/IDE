# Service Layer Analysis

## Overview
Analysis of service layer: `container_service.py`, `class_service.py`, `file_service.py`, `folder_service.py`, `function_service.py`, `project_service.py`.

---

## 🔴 Critical Issues

### 1. Duplicated `delete` Pattern Across Services
**Files**: `class_service.py:37-48`, `file_service.py:107-118`, `folder_service.py:25-36`, `function_service.py:36-47`

All four have **identical** delete logic:

```python
async def delete(self, node_key: str):
    node_id = f"nodes/{node_key}"
    descendants = await self.repos.xxx_repo.get_containment_tree(node_id, depth="*")
    descendant_keys = [item["vertex"]["_key"] for item in descendants]
    for key in reversed(descendant_keys):
        await self.repos.nodes.delete(key)
    return await self.repos.xxx_repo.delete(node_key)
```

**Solution**: Move to `ContainerService` base class with generic implementation.

---

### 2. Duplicated `get_code` Pattern
**Files**: `class_service.py:74-101`, `function_service.py:73-100`

Both have ~25 lines of identical logic:

```python
async def get_code(self, node_id: str):
    node = await self.repos.xxx_repo.get_by_id(node_id)
    if not node:
        return None
    file_doc, project_doc = await self._resolve_file_and_project(node.id)
    if not file_doc or not project_doc:
        return None
    abs_path = await self._build_abs_file_path(...)
    code = await self._extract_code_from_file(abs_path, node.position)
    return {...}
```

**Solution**: Create generic `_get_code_for_positioned_node()` in `ContainerService`.

---

### 3. Duplicated `add_*` Methods
**Pattern repetition across services**:

| Service | Methods |
|---------|---------|
| `ClassService` | `add_function`, `add_call`, `add_class` |
| `FileService` | `add_function`, `add_call`, `add_class` |
| `FunctionService` | `add_function`, `add_call`, `add_class` |
| `FolderService` | `add_folder`, `add_file` |
| `ProjectService` | `add_folder`, `add_file` |

Each is a thin wrapper:
```python
async def add_function(self, parent_id: str, function_id: str):
    return await self.add_child_to_container(parent_id, function_id, "xxx_to_function")
```

**Question**: Are these needed? They just add type-specific edge labels.

**Recommendation**: Consider removing in favor of direct `add_child_to_container()` calls with edge type inference (already exists in `ContainerService.add_child_to_container` lines 37-40).

---

## 🟡 Design Issues

### 4. Missing Parent Class `__init__` Call
**Files**: All service classes

```python
class ClassService(ContainerService):
    def __init__(self, repos: Repositories):
        self.repos = repos  # ❌ Should call super().__init__(repos)
```

**Problem**: Not calling parent `__init__` - works by accident because parent also sets `self.repos`.

---

### 5. Async Method That Doesn't Need to Be Async
**File**: `container_service.py:146-152`

```python
async def _build_abs_file_path(self, project_path: str, file_path: str) -> str:
    import os
    if os.path.isabs(file_path):
        return file_path
    return os.path.normpath(os.path.join(project_path, file_path))
```

This is pure synchronous path manipulation - no `await` used.

---

### 6. `rebuild_call_group` Complexity
**File**: `container_service.py:214-282`

68 lines of complex logic that:
1. Gets children
2. Filters call nodes
3. Finds existing call groups
4. Deletes old group
5. Creates new group

**Suggestion**: Extract into dedicated `CallGroupService` or move to a use-case/orchestrator layer.

---

### 7. `ProjectService.get_children` vs `get_project_structure`
**File**: `project_service.py:49-67`

Two methods with nearly identical logic, differing only in depth:

```python
async def get_children(self, project_id, exclude_groups=False):
    return await self.repos.project_repo.get_containment_tree(project_id, 50, ...)

async def get_project_structure(self, project_id, exclude_groups=False):
    return await self.repos.project_repo.get_containment_tree(project_id, depth="*", ...)
```

**Solution**: Single method with `depth` parameter.

---

## 🟢 Improvement Recommendations

### Step 1: Generic Delete in ContainerService

```python
# container_service.py
async def delete_with_descendants(self, node_key: str) -> bool:
    """Generic cascading delete for any container node."""
    node_id = f"nodes/{node_key}"
    descendants = await self.repos.nodes.get_containment_tree(node_id, depth="*")
    descendant_keys = [item["vertex"]["_key"] for item in descendants]
    for key in reversed(descendant_keys):
        await self.repos.nodes.delete(key)
    return await self.repos.nodes.delete(node_key)
```

### Step 2: Generic get_code in ContainerService

```python
async def get_code_for_node(self, node_id: str) -> Optional[Dict]:
    """Get code for any positioned node (function, class, call)."""
    node = await self.repos.nodes.get_by_id(node_id)
    if not node or not hasattr(node, 'position'):
        return None
    # ... shared logic
```

### Step 3: Remove Redundant add_* Methods

Keep only `add_child_to_container()` in base class - it already auto-generates edge type.

### Step 4: Fix Inheritance

```python
class ClassService(ContainerService):
    def __init__(self, repos: Repositories):
        super().__init__(repos)  # ✓ Proper inheritance
```

---

## Summary

| Category | Count |
|----------|-------|
| Duplicated delete methods | 4 |
| Duplicated get_code methods | 2 |
| Thin wrapper methods | 15+ |
| Missing super().__init__ | 6 |
| **Estimated LOC reduction** | **~100 lines** |
