# Logger

Because we track every function and class and maintain a live call graph, V‑NOC captures rich, structured logs and links them directly to their owners. You get per‑function performance, inputs/outputs, and custom events and errors — all organized in a clear call hierarchy instead of a flat stream. That means faster debugging, effortless end‑to‑end tracing, and logs that actually tell the story of your code.

![Logger](/assets/logs.png)

## Example: Hierarchical log

Below is a simplified view of a request where function `A` calls function `B`. The logger captures ENTER/EXIT events and a WARNING inside `B`, preserving the call hierarchy:

```text
REQUEST 42
└─ A ENTER args={...}
   ├─ log      msg="starting A"
   ├─ call B
   │  └─ B ENTER args={...}
   │     ├─ warn     msg="unexpected input; using default"
   │     └─ B EXIT   return={value} duration=12ms
   └─ A EXIT return={ok} duration=20ms
```

Legend:
- ENTER/EXIT: auto-captured function boundaries with timing and return values
- log/warn: your custom messages at any level in the call
- call: indicates a nested invocation; children are indented under the caller

