# API Layer Analysis

## Overview
Analysis of API routes: `code_element.py`, `container.py`, `projects/crud.py`.

---

## 🔴 Critical Issues

### 1. Duplicate Route Definitions in `projects/crud.py`
**Lines 95-101 and 146-151**:

```python
@router.get("/", response_model=list[ProjectNode])  # Line 95
async def get_projects(...):
    projects = await project_service.get_all()
    return projects

@router.get("/", response_model=list[ProjectTreeNode])  # Line 146 
async def get_all_projects(...):
    projects = await project_service.get_all()
    return projects
```

**Problem**: Two handlers for the same `GET /` route. FastAPI uses the first match, so `get_all_projects` is **unreachable dead code**.

**Solution**: Remove one of them.

---

### 2. Inconsistent Service Acquisition Pattern
**File**: `code_element.py`

```python
# Pattern 1: Helper function (lines 32-44)
def _get_services(db: AsyncDatabase):
    project_service = get_project_service(db)
    file_service = get_file_service(db)
    ...
    return (project_service, file_service, ...)

# Usage in handlers:
project_service, file_service, _, _, _ = _get_services(db)

# Pattern 2: Direct injection (line 133)
@router.post("/{project_id}/run-code")
async def run_code(project_service: ProjectService = Depends(get_project_service)):
```

**Problem**: Two different patterns in same file.

**Solution**: Use dependency injection consistently.

---

## 🟡 Design Issues

### 3. Repository Access in API Layer
**File**: `code_element.py:61-67, 90-100`

```python
# API handler directly accesses repository
node_repo = Repositories(db).nodes
raw_node = await node_repo.get_raw_by_key(element_id)
```

**Problem**: API layer should only interact with services, not repositories directly. Violates layered architecture.

**Solution**: Add `get_node_by_key()` method to a service.

---

### 4. Mixed Concerns in `write_code` Endpoint
**File**: `code_element.py:47-78`

This endpoint does too much:
1. Gets service references
2. Manually accesses repository
3. Walks up to find project
4. Starts file watcher
5. Writes code

**Solution**: Move watcher logic to service layer.

---

### 5. Endpoint Naming Inconsistency

| Endpoint | Naming Style |
|----------|--------------|
| `/{element_id}/write-code` | kebab-case |
| `/{element_id}/code` | single word |
| `/{project_id}/run-code` | kebab-case |
| `/{container_id}/update-theme` | kebab-case |
| `/{container_id}/update-basic-info` | kebab-case |

**Recommendation**: Standardize. REST convention is kebab-case for paths.

---

### 6. Response Model Inconsistencies

| File | Endpoint | Response Model |
|------|----------|----------------|
| `crud.py` | `GET /` | `list[ProjectNode]` |
| `crud.py` | `GET /` (duplicate) | `list[ProjectTreeNode]` |
| `crud.py` | `GET /{id}` | `ProjectTreeNode` |
| `crud.py` | `DELETE /{id}` | `bool` |

**Issue**: `DELETE` returning `bool` instead of standard 204 No Content.

---

## 🟢 Folder Structure Recommendations

### Current Structure
```
api/core/
├── __init__.py
├── code_element.py    # Mixed: element code + run code
├── container.py       # Container theme/info updates
├── logger.py
└── projects/
    ├── __init__.py
    └── crud.py        # All project operations
```

### Recommended Structure
```
api/
├── __init__.py
├── v1/                # Version your API
│   ├── __init__.py
│   ├── projects/
│   │   ├── __init__.py
│   │   ├── routes.py      # Route definitions only
│   │   └── schemas.py     # Request/Response models
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── schemas.py
│   ├── containers/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── schemas.py
│   └── code/
│       ├── __init__.py
│       ├── routes.py      # get_code, write_code, run_code
│       └── schemas.py
└── dependencies.py        # Shared DI functions
```

---

## 🔧 Step-by-Step Improvements

### Step 1: Remove Duplicate Route
Delete either `get_projects` or `get_all_projects` from `crud.py`.

### Step 2: Move Repository Access to Services
```python
# Before (in API):
node_repo = Repositories(db).nodes
raw_node = await node_repo.get_raw_by_key(element_id)

# After (add to ContainerService):
async def get_node_type(self, element_id: str) -> Optional[str]:
    raw = await self.repos.nodes.get_raw_by_key(element_id)
    return raw.get("node_type") if raw else None
```

### Step 3: Consistent Dependency Injection
```python
# Replace _get_services() helper with proper DI
@router.post("/{element_id}/write-code")
async def write_code(
    element_id: str,
    code_block: str = Body(...),
    file_service: FileService = Depends(get_file_service),
    watcher_service: WatcherService = Depends(get_watcher_service),
):
    ...
```

### Step 4: Return 204 for DELETE
```python
from fastapi import Response

@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, ...):
    ...
    return Response(status_code=204)
```

---

## Summary

| Category | Count |
|----------|-------|
| Duplicate routes | 1 |
| Repository access in API | 2 locations |
| Inconsistent patterns | 3 |
| Naming inconsistencies | Minor |
