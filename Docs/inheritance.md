## Inheritance

V‑NOC maps class relationships and resolves method lookup using Python’s C3 linearization (MRO). This shows which methods are inherited, overridden, or reached via `super()`.

### What we analyze

* Base and derived class relationships
* Method overrides and `super` calls
* MRO ordering to determine the effective method at call time

### Why it matters

* See exactly which implementation will run and why
* Understand how a change in a base class affects subclasses
* Avoid subtle bugs in multiple‑inheritance hierarchies

![Inheritance MRO](/assets/base_class_mro.png)


