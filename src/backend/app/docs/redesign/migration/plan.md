### Incremental Migration Plan

Phase 1: Foundations
- Introduce repositories and UoW behind feature flags
- Implement GraphWriter with no-op adapters

Phase 2: Dual-Run
- Route a subset of writes through repositories+UoW
- Mirror reads with new read repos in shadow mode

Phase 3: Cutover
- Switch services to use repositories/UoW by default
- Retire direct collection access from domain

Phase 4: Hardening
- Add validators and background integrity checks
- Add metrics dashboards and alerts

## Step-by-step: Execute a migration

Checklist
- [ ] Add `model_version` field to nodes
- [ ] Create required indices
- [ ] Deploy GraphWriter and UoW
- [ ] Backfill `qname` for legacy nodes

Example script (pseudo)
```python
for doc in db.nodes.all():
    if "model_version" not in doc:
        doc["model_version"] = 2
        db.nodes.update(doc)
``` 