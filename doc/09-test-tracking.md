# 09 · Test Tracking

V-NOC treats tests as **first-class graph data**. A test isn't just a file in `tests/` — it's an edge from a test case to the function or class under test. When you click a function, you immediately see what covers it; when a test fails, you immediately see which symbol it was exercising.

---

## What V-NOC tracks

| Concept | Graph shape | Where it lives |
|---|---|---|
| **Test config** | One per project (framework, command, root dir, env) | `GET/POST/PUT/DELETE /api/v1/tests/config` |
| **Test case** | Node — discovered or registered | `GET /api/v1/tests/cases` |
| **Coverage edge** | Test case → covered symbol(s) (function/class node) | Inferred from runs |
| **Run** | Snapshot of a test execution (status, duration, output) | `POST /api/v1/tests/run` |

All endpoints live in `src/backend/app/api/v1/test_routes.py`, backed by `test_service`.

---

## 1. Configure once per project

Tell V-NOC how your tests are run:

```http
POST /api/v1/tests/config
```

Body specifies:

- **Framework** (`pytest`, `vitest`, etc.)
- **Command** to invoke (e.g. `pytest -q`)
- **Working directory** (relative to the project path)
- **Environment** variables to inject

V-NOC stores this on the project node, so anyone else opening the project gets the same setup.

---

## 2. Discover and link cases

After parsing, V-NOC walks the test directory through the same language driver pipeline. Each test function/class is materialised as a graph node and given a stable ID like any other function (see `06-function-class-tracking.md`).

Coverage edges are discovered three ways:

1. **Static analysis** — the parser follows imports and calls from the test into the project code.
2. **Runtime tracing** — when a test runs, V-NOC records which symbols were exercised and adds/updates `covers` edges.
3. **Manual pinning** — you can drag a node onto a test case in the UI to assert "this test covers this symbol".

---

## 3. Run them

From the canvas, click **Run** on a project, a symbol, or a single case:

```http
POST /api/v1/tests/run
```

You can scope the run:

- **All** — entire suite from the configured command
- **By symbol** — runs only cases with a `covers` edge to the selected node(s)
- **By case** — runs a hand-picked subset

The streamed output appears beside the test node; the final status (pass/fail/error/skip) is stored as a new run node attached to the case.

---

## 4. Read the results

| View | Use |
|---|---|
| **Coverage panel** on a function node | Which cases cover it? When did each last pass? |
| **Test panel** on a case | Recent runs, last failure output, the symbols it covers |
| **Project dashboard** | Aggregate pass/fail across the latest run |

Because cases and symbols are stable nodes, a failed run on `commit_a` and a passed run on `commit_b` show up side-by-side on the same case node — see `10-version-control.md`.

---

## How it differs from a CI dashboard

A CI dashboard tells you which files changed and which tests failed. V-NOC tells you:

- Which **symbols** are now uncovered after a refactor.
- Which **call paths** through the graph reach a failing assertion.
- Which **playgrounds** correspond to the failing case (often a useful reproduction).
- Whether a fix in commit B truly addresses the failure in commit A, by comparing the symbol-level diff to the test that broke.

---

## Local CLI tests

The backend's own test suite runs without any of this machinery:

```bash
make test-backend
```

That executes `pytest -s tests` inside `src/backend/`. See `03-getting-started.md`.

Next: [10 · Version Control (TerminusDB)](10-version-control.md).
