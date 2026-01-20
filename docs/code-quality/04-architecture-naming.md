# Architecture & Naming Conventions

## Overview
Analysis of folder structure, naming conventions, and architectural patterns.

---

## 📁 Current Folder Organization

```
src/backend/app/
├── api/
│   └── core/
│       ├── code_element.py
│       ├── container.py
│       ├── logger.py
│       └── projects/
│           └── crud.py
├── core/
│   ├── model/
│   ├── repository/
│   │   ├── base/
│   │   │   ├── base_collection.py
│   │   │   └── node_repo.py
│   │   ├── code_elements/
│   │   │   ├── call_repo.py
│   │   │   ├── class_repo.py
│   │   │   └── function_repo.py
│   │   ├── file_repo.py
│   │   ├── folder_repo.py
│   │   └── project_repo.py
│   └── services/
│       ├── class_service.py
│       ├── container_service.py
│       ├── file_service.py
│       ├── folder_service.py
│       ├── function_service.py
│       └── project_service.py
└── db/
```

---

## 🔴 Issues

### 1. Inconsistent Repository Organization
```
repository/
├── base/           # ✓ Good: base classes in subfolder
├── code_elements/  # Has: call, class, function repos
├── file_repo.py    # ❌ Why not in code_elements/ or structure/?
├── folder_repo.py  # ❌ Same issue
└── project_repo.py # ❌ Same issue
```

**Problem**: `file_repo`, `folder_repo`, `project_repo` are at root level while similar repos (`class`, `function`, `call`) are in `code_elements/`.

**Options**:
1. Move `file_repo`, `folder_repo` to a `structure/` subfolder
2. Flatten everything to root (simpler)
3. Organize by domain: `project/`, `filesystem/`, `code/`

---

### 2. API Structure Inconsistency
```
api/core/
├── code_element.py  # Single file
├── container.py     # Single file
├── logger.py        # Single file
└── projects/        # Folder with crud.py
    └── crud.py
```

**Problem**: `projects` is a folder, others are files. Inconsistent.

---

### 3. Naming Convention Violations

| File/Class | Issue |
|------------|-------|
| `crud.py` | Generic name - should be `routes.py` or `endpoints.py` |
| `code_element.py` | Should be `code_elements.py` (plural) or `code/routes.py` |
| `container_service.py` | Good |
| `node_repo.py` | In `base/` but is actually the main repo |

---

### 4. Missing Domain Separation

**Current**: Repositories are organized by technical type (file, folder, project)

**Better**: Organize by domain/feature:

```
repository/
├── base/
├── project/           # Project domain
│   ├── project_repo.py
│   └── structure_repo.py  # files, folders
└── code/              # Code analysis domain
    ├── element_repo.py    # functions, classes
    └── call_repo.py
```

---

## 🟢 Recommended Structure

### Option A: Feature-Based (Recommended)

```
src/backend/app/
├── api/
│   ├── __init__.py
│   ├── dependencies.py
│   └── v1/
│       ├── projects/
│       │   ├── routes.py
│       │   └── schemas.py
│       ├── nodes/
│       │   ├── routes.py
│       │   └── schemas.py
│       └── code/
│           ├── routes.py
│           └── schemas.py
├── domain/              # Business logic layer
│   ├── project/
│   │   ├── service.py
│   │   ├── repository.py
│   │   └── models.py
│   ├── filesystem/
│   │   ├── service.py
│   │   ├── repository.py
│   │   └── models.py
│   └── code_elements/
│       ├── service.py
│       ├── repository.py
│       └── models.py
└── infrastructure/
    ├── database/
    └── cache/
```

### Option B: Minimal Cleanup (Less Disruption)

```
src/backend/app/
├── api/core/
│   ├── projects/
│   │   └── routes.py       # Renamed from crud.py
│   ├── nodes/
│   │   └── routes.py       # Split from code_element.py
│   ├── code/
│   │   └── routes.py       # Code operations
│   └── containers/
│       └── routes.py       # From container.py
├── core/
│   ├── repository/
│   │   ├── base/
│   │   ├── structure/      # file, folder repos
│   │   │   ├── file_repo.py
│   │   │   └── folder_repo.py
│   │   ├── project_repo.py
│   │   └── code_elements/  # Keep as-is
│   └── services/           # Keep as-is
```

---

## 📝 Naming Conventions

### Files
| Current | Recommended | Reason |
|---------|-------------|--------|
| `crud.py` | `routes.py` | Descriptive of content |
| `code_element.py` | `code_routes.py` | Consistent with others |
| `node_repo.py` | `base_node_repo.py` | Clarify it's a base class |

### Classes
| Current | Status |
|---------|--------|
| `FileRepo` | ✓ Good |
| `FileService` | ✓ Good |
| `NodeRepository` | ✓ Good (but consider `BaseNodeRepository`) |
| `ContainerService` | ✓ Good (base class) |

### Methods
| Current | Issue | Recommended |
|---------|-------|-------------|
| `get_by_qnames` | OK | - |
| `get_children` | OK | - |
| `add_child_to_container` | Verbose | `add_child` |
| `delete_batch` | OK | - |
| `find_call_by_target_parent` | Long | `find_call` with params |

---

## Summary

| Category | Recommendation |
|----------|----------------|
| Folder organization | Consolidate repos into subfolders by domain |
| File naming | Rename `crud.py` → `routes.py` |
| Class naming | Prefix base classes with `Base` |
| API versioning | Add `/api/v1/` prefix |
