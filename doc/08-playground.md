# 08 · Playground

A **Playground** is a sandboxed snippet of code attached to a specific node in the graph — a function, a class, a file, or a folder. It lets you exercise that piece of code **in isolation**, without booting the rest of the app, and pin the results to the node so they're rediscoverable.

This is V-NOC's "if the power supply fails, fix the power supply" feature: a focused workbench for one thing at a time.

---

## What a playground is

| Attribute | Description |
|---|---|
| Owner node | A function, class, file, or folder in the graph |
| Body | The snippet of code (Python, today) that runs against the owner |
| Inputs | Captured per-run: arguments, env, deps |
| Outputs | Return value, stdout/stderr, raised exceptions, duration |
| History | Each run is stored; old runs remain visible for comparison |

A playground inherits its owner's **context** — imports, types, fixtures — so you can call the function under test without re-wiring boilerplate.

---

## Creating one

From the canvas: select a node, open the **Playground** panel, click **New Playground**. Behind the scenes:

```http
POST /api/v1/playgrounds/
```

Body identifies the owner node and supplies the snippet. The endpoint is implemented in `src/backend/app/api/v1/play_ground_routes.py`, backed by `play_ground_service` and the sandbox executor at `src/backend/app/core/sandbox/code_run.py`.

You can list playgrounds for a node:

```http
GET /api/v1/playgrounds/owners/{owner_node_id}
```

Update, delete, and re-run as expected:

```http
PUT    /api/v1/playgrounds/{playground_id}
DELETE /api/v1/playgrounds/{playground_id}
POST   /api/v1/playgrounds/run-code
```

---

## Why playgrounds, not REPLs

A REPL is global. A playground is **local to a node**, which means:

- It's pinned next to the code it exercises, so the next person sees how that function is meant to be poked.
- Inputs and outputs accumulate as **examples** — useful for tests, docs, and AI agents that need a concrete usage shape.
- Refactoring the owner node updates the playground's binding automatically (same node ID, see `06-function-class-tracking.md`).

---

## Safety

Snippets run inside the sandbox executor (`code_run.py`). The sandbox:

- Imports run from the owner's project path so relative imports resolve.
- Captures stdout/stderr; long-running runs are time-boxed.
- Does **not** restrict filesystem or network access today — treat playgrounds as if they were arbitrary code you wrote yourself, because they are.

> [!WARNING]
> Do not check secrets into playgrounds. They're stored in TerminusDB and travel with the project.

---

## When to use one

- Reproducing a bug on a single function before reaching for the debugger.
- Capturing canonical "this is how to call it" examples for downstream consumers.
- Generating fixtures for a test (see `09-test-tracking.md`) — convert a passing playground into a test case in one click.
- Letting an AI agent dry-run a change without committing it.

Next: [09 · Test Tracking](09-test-tracking.md).
