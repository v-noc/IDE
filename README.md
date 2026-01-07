
# V-NOC (Visual Node Code) — *Placeholder Name*

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

**A code editor that shows you how your code *works*, not just where it's saved.**

**Community & Support:** Join our Discord — [discord.gg/NKhbU9gf](https://discord.gg/J5nfPHqyBr)

![V-NOC](/assets/logs.png)

### The Problem: The Invisible Weight of Code

Every developer knows the feeling. You're dropped into a large, unfamiliar codebase, and your first task is to build a map in your head. You trace function calls across dozens of files, trying to remember:

*   Where is this function defined? What other functions call it?
*   What happens if I change this one line of code? What are the downstream effects?
*   How does data flow from the initial API request all the way to the database?
*   To debug an issue, you jump between your editor, a terminal for logs, a browser for documentation, and maybe another tool for performance metrics.

This "mental model" is powerful, but it's also fragile, invisible, and takes a huge amount of cognitive effort to build and maintain. Our current tools, based on a static list of files and folders, force us to do this complex work in our heads. The file system organizes where code is *stored*, but it does nothing to explain how it all *connects*.

### The Solution: A Living Map of Your Code

**V-NOC** is designed to solve this problem by taking that complex mental model out of your head and putting it onto your screen.


Instead of a file tree, the core of V-NOC is a **living, interactive graph**. It analyzes your code to understand its structure and simulates its execution paths to build a visual map of your entire project.

*   **Nodes** in the graph are your functions, classes, modules, or even files.
*   **Edges** are the connections between them—the function calls, dependencies, and relationships that define how your application actually works.

This approach frees you from the limitations of the file system and allows you to navigate your code based on its logic, not its location.

### What This Unlocks

**1. Instant Understanding, Zero Overhead**  
The code graph is your single source of truth. You can instantly see the entire call stack for a feature, identify dependencies, and understand the impact of a change without manually tracing anything. This dramatically reduces the mental overhead required to work on large projects, especially for new team members.

**2. All Information, Where You Need It**  
V-NOC aims to be a unified knowledge base for your code. Every node in the graph is a container for all the context related to it. You can attach everything you need directly to a function or class:
*   **Documentation & Notes:** Keep explanations right next to the code they describe.
*   **[Logs](/src/vn_logger/) & Traces:** See the execution history of a specific function.
*   **Test Results & Performance Metrics:** Understand its reliability and speed.

This eliminates constant context-switching. All the information you need to understand, debug, or build upon a piece of code is available in one place.

**3. [Logs](/src/vn_logger/) That Make Sense (Hierarchical Logs)**  
Traditional logs are a flat, scattered list of messages, making it difficult to trace the flow of a single request. V-NOC introduces **hierarchical logs**.

[Logs](/src/vn_logger/) are organized into a **tree structure that perfectly mirrors the code's call graph**. When a request comes in, you see the top-level log. You can then unfold it to see the logs from every function it called, in the exact order they were executed. Finding the source of an error becomes as simple as navigating a tree, not searching through a messy text file.

**4. A Superpower for Humans and AI**  
By structuring code and its context in a graph, V-NOC makes development more intuitive for programmers. It also makes codebases far easier for AI models (LLMs) to understand. An AI can query the graph to get a function, its complete call history, its documentation, and its recent logs, giving it all the context it needs to make intelligent, accurate changes without parsing thousands of files.


## Usage

This is not ready for production use. If you want to experiment, open `examples/sample_project` — the code is minimal and meant to demonstrate the core ideas.

`v-noc.toml` is required. Because browsers cannot read absolute paths from the local file system, use it to provide the absolute project path via `pwd={project_path}` when creating a project.

Nodes are extracted via an AST parser. Coverage is intentionally limited for now.

### Supported

* **Functions and classes**
* **Call relationships**
  * Functions
    * Callbacks
    * Factory closures
    * Imports (`import`, `from ... import ...`)
    * Assignments and resolution (variable aliasing for calls)
  * Classes
    * Instantiation (constructor)
    * `self` calls
    * `super` calls
    * Imports (`import`, `from ... import ...`)
    * Assignments and resolution (instance aliasing for method calls)
    * Object method calls (e.g., `obj.method()`)
    * Inheritance method resolution (C3 linearization)

### Limitations (Not Yet Supported)

* Recursive call detection
* Collections handling: arrays/lists, tuples, dicts
* Type extraction/inference
* Conditional or multiple assignments to the same variable, e.g.:

  ```python
  if type == "pdf":
      reader = pdf.reader
  else:
      reader = text.reader
  reader()
  # or
  reader = pdf.reader if type == "pdf" else text.reader
  reader()
  ```

* Calls inside argument positions (nested calls), e.g. `caller(fn())`

## Technologies used

* **Current stack (rapid prototyping)**
  * Backend: `Python` (`FastAPI`)
    * Why: fast to iterate, great async support, rich ecosystem (Pydantic, uvicorn), and easy integration with LLM agents.
    * Responsibilities: parse source code, build the code graph, expose APIs (REST/JSON-RPC), and coordinate project/file watching.
  * Frontend: `React`
    * Why: rapid UI iteration, strong component model, mature graph visualization and editor integrations.
    * Responsibilities: interactive code graph, code editor, settings and diagnostics UI, log/views.
* **Database**: `ArangoDB`
  * Why: native graph database plus document/key-value in one engine fits nodes/edges and attached metadata/logs.
  * Responsibilities: store projects, files, nodes, edges, and logs; support queries like call graphs, dependents, and impact analysis via AQL traversals.
* **Planned migration**
  * Full rewrite in `Rust` with `Tauri`, targeting desktop and web apps.
    * Why: performance for indexing and file watching, lower latency and footprint, single codebase for desktop/web.
    * Migration plan:
      1. Extract the indexer/watcher into a Rust library, optionally bridged from Python.
      2. Replace backend services with Rust while preserving API boundaries.
      3. Ship a desktop app via Tauri; reuse the UI and expose the core to web (WASM) where applicable.


## Quick Start (Setup & Install)

### Prerequisites
- **Python** 3.11+ and **uv**
- **Node.js** 18+ and **Yarn**
- **Docker** and **Docker Compose** (for the database)

### 1) Create Python virtual environment
```bash
uv venv .venv
```

### 2) Install dependencies
- **All (backend + frontend)**
```bash
make install
```

- **Backend only**
```bash
make install-backend
```

- **Frontend only**
```bash
make install-frontend
```

### Optional: Database container
```bash
make start-db   # start ArangoDB
make stop-db    # stop ArangoDB
```

See the `Makefile` for additional commands.

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).

- Community use: Free under AGPL-3.0 (with copyleft obligations).
- Commercial/proprietary use (e.g., closed-source modifications, SaaS without source release): Available under a separate license — contact [your.email@example.com] for details.

Full license: [LICENSE](LICENSE) file or https://www.gnu.org/licenses/agpl-3.0.html

