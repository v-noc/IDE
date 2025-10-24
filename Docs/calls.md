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

### Examples

Direct call

```python
def b():
    return "ok"

def a():
    return b()

a()
```

```text
a()
└─ b()
```

Callback

```python
def runner(fn):
    return fn()

def callback():
    return "done"

def a():
    return runner(callback)

a()
```

```text
a()
└─ runner(fn)
   └─ callback()
```

Factory closure

```python
def make_greeter(name: str):
    def greet():
        return f"hi {name}"
    return greet

def a():
    g = make_greeter("Ada")
    return g()

a()
```

```text
a()
└─ make_greeter("Ada") -> g
   └─ g()  [closure: greet]
```

Method call on an object

```python
class Service:
    def work(self):
        return "ok"

def a():
    s = Service()
    return s.work()

a()
```

```text
a()
├─ Service.__init__()
└─ s.work()  -> Service.work
```

![Isolate function](/assets/isolate_function.png)


