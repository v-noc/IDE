## Calls

V‑NOC builds a precise call graph so you can see how execution really flows across functions, files, and modules.

### What we analyze

* Direct calls between functions
* Callbacks and factory closures
* Method calls on objects (e.g., `obj.method()`)
* Imports used by the focused code path

### Why it matters

* Understand end‑to‑end request flow without manual tracing
* Perform impact analysis: find all callers and dependents instantly
* Spot dead code and risky dependencies early

### Use cases

* Isolate a function and bring only its dependencies into a sandbox to test or share
* Review a feature by navigating its actual call chain, not the file tree
* Guide LLMs with precise, minimal context from the exact slice of code

![Isolate function](/assets/isolate_function.png)


