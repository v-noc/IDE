# Phase 3 / Step 1 — Lean DB snapshot

New: `graph_builder/discovery/db_snapshot.py`

## Shape (top)

```python
@dataclass(frozen=True)
class SnapshotRow:
    id: str
    path: str
    hash: Optional[str]        # files only
    kind: Literal["file", "folder", "group"]

@dataclass
class DbSnapshot:
    rows_by_id: dict[str, SnapshotRow]
    ids_by_path: dict[str, str]
    ids_by_hash: dict[str, list[str]]     # duplicate contents allowed
    resolver: GroupResolver               # parent edges loaded in the same pass

    @classmethod
    async def load(cls, repos) -> "DbSnapshot": ...
```

One object handed to ChangeDetector + id resolution + move policy. Replaces:

- `get_all(FileSchema)` / `get_all(FolderSchema)` full-doc loads (change_detector.py:365)
- `_build_parent_maps` folder-children parsing
- ad-hoc `get_snapshot_rows` from Phase 1 (subsumed)

## The query (middle)

Two triple-selects (or one with `or`), zero `read_document`:

```
# nodes: id, type, path, hash
select v:id, v:type, v:path, v:hash
  where v:id rdf:type v:type,
        v:type in [@schema:FileSchema, @schema:FolderSchema, @schema:StructureGroupSchema],
        v:id path v:path            (opt — groups have no path)
        opt(v:id hash v:hash)

# edges: parent, field, child      ← already specified in Phase 1 GroupResolver.load
```

Payload ≈ 4 small strings per node instead of full documents with children sets and
metadata. For a 10k-file project this is the difference between ~2 MB and ~50+ MB per
resync.

Exclude `INIT_FOLDER_ID` rows here (single place, instead of change_detector.py:371).

## Memory notes

- `ids_by_hash` only for files, values are lists (vendored duplicates share hashes) —
  used by step 02's moved-file fast path; collisions resolved by preferring a row whose
  old path's basename matches.
- Snapshot is per-sync and dropped at the end; no cross-sync caching here (that is the
  id-cache in step 02, which is tiny).

## Steps (bottom)

1. Implement `DbSnapshot.load` on top of the `get_edge_triples` helper from Phase 1
   (extend it to also return node scalar triples).
2. Switch `ChangeDetector.detect_changes` to consume `DbSnapshot`
   (constructor param or method arg — prefer method arg; detector becomes stateless).
3. Delete the `get_all` calls and `_build_parent_maps`.
4. Assert equivalence: fixture project → old path vs new path produce identical
   ChangeSets (write a one-off comparison test, keep it until Phase 3 ships).
