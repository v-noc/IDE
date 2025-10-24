## Focus mode

Focus mode lets you isolate a single node and its most relevant relationships so you can work without visual noise. Instead of rendering the entire project graph, it shows the selected node and a small, configurable neighborhood around it.

![Focus mode](/assets/focus.png)

### What’s included

* The selected node (function, class, module, or file)
* Direct callees and callers (outgoing and incoming calls)
* Class relationships (base/derived classes, `super` calls)
* Imports used by the focused node
* Optionally, immediate children such as methods or nested definitions

### Why it helps

* Reduces cognitive load by hiding unrelated parts of the graph
* Speeds up debugging and impact analysis around a specific function or class
* Makes code reviews and demos clearer by showing only the relevant slice

### Non‑destructive by design

The view uses virtual nodes/edges for presentation only. Changing the focus does not modify your source files or project structure.

