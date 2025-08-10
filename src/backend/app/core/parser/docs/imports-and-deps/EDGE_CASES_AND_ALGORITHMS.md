### Imports & Dependencies: Edge Cases and Algorithms

#### Edge cases to support
- Aliases: `import numpy as np`
- From-imports: `from fastapi import Request as R`
- Relative imports: `from .base import X`, `from ..pkg import Y`
- Multi-imports: `from pkg import a, b as bb`
- Star imports: `from pkg import *` (record issue; avoid implicit expansion)
- Package vs local module with same top-level name
- Attribute chains: `np.random.rand`, `requests.get().json`
- Re-exports: `from pkg.sub import name as name` at package `__init__`

#### Resolution algorithm (per file)
1) Build import map (alias → qname)
   - Absolute: `alias → moduleOrSymbol`
   - Relative: compute base from module qname and level
2) Usage `Name(id)`
   - If `id` in import map: create UsesImport edge to qname
3) Usage `Attribute(base.attr)`
   - Reconstruct chain
   - If base is in import map → try `qname = importQ + '.' + rest`
     - If `SymbolIndex.resolve(any, qname)` → edge to qname
     - Else edge to base import qname (module/class) and record issue RES3001
4) Distinguish package vs local
   - If `SymbolIndex.modules.has(prefix)` → local
   - Else treat as external package; create/get package node for top-level

#### Star imports
- Do not expand
- Record `Issue code=IMP1001` with span; optionally consult type stubs to disambiguate in future

#### Re-exports
- If analyzing packages, allow a package index to contain alias entries for `__all__` or discovered exports

#### Diagnostics
- Collect issues for unresolved imports, ambiguous names, invalid relative levels

#### Persistence
- Edges are stored per consumer (function/class) with import and usage positions 