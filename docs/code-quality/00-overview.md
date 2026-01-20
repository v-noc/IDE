# Code Quality Analysis Overview

## Purpose
Step-by-step analysis and improvement plan for the backend codebase across repositories, services, and API layers.

---

## Documents

| Document | Focus Area | Key Findings |
|----------|-----------|--------------|
| [01-repository-layer.md](./01-repository-layer.md) | Repository pattern | 12+ duplicated methods, inconsistent return types |
| [02-service-layer.md](./02-service-layer.md) | Service classes | Duplicated delete/get_code, 15+ thin wrappers |
| [03-api-layer.md](./03-api-layer.md) | FastAPI routes | Duplicate routes, repo access in API layer |
| [04-architecture-naming.md](./04-architecture-naming.md) | Folder structure | Inconsistent organization, naming issues |

---

## Priority Matrix

### 🔴 Critical (Fix First)
1. **Duplicate route** in `projects/crud.py` - causes dead code
2. **`delete_batch` duplication** across 4 repos - ~60 LOC waste
3. **Repository access in API** - architecture violation

### 🟡 Medium Priority
4. **Consolidate `get_by_qnames` / `get_by_ids`** to base repo
5. **Create generic `delete_with_descendants`** in ContainerService  
6. **Fix missing `super().__init__`** in all services

### 🟢 Nice to Have
7. Reorganize folder structure
8. Rename `crud.py` → `routes.py`
9. Add API versioning

---

## Estimated Impact

| Metric | Before | After (Est.) |
|--------|--------|--------------|
| Duplicated LOC | ~250 | ~50 |
| Repo methods | 45+ | ~30 |
| Service methods | 60+ | ~40 |
| Dead code | 1 route | 0 |

---

## Implementation Order

```
Phase 1: Quick Wins (1-2 hours)
├── Remove duplicate route in crud.py
├── Fix missing super().__init__ calls
└── Remove unreachable wrapper methods

Phase 2: Repository Cleanup (2-3 hours)
├── Add get_by_ids(), get_by_qnames() to NodeRepository
├── Delete duplicates from child repos
└── Standardize delete_batch return type

Phase 3: Service Cleanup (2-3 hours)
├── Add delete_with_descendants() to ContainerService
├── Add get_code_for_node() to ContainerService
└── Remove thin wrappers (if safe)

Phase 4: API & Architecture (Optional, larger effort)
├── Move repo access to services
├── Reorganize folder structure
└── Add API versioning
```

---

## Next Steps

1. Review each document for detailed analysis
2. Decide which patterns to implement
3. Create implementation PRs per phase
