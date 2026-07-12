# Parser Refactor: Language-Agnostic Driver Architecture

## Problem

The current parser (`src/backend/app/core/parser/`) is tightly coupled to Python-specific
libraries — **parso** (AST building), **libcst** (ID injection / CST transforms), and **jedi**
(MRO resolution, call hierarchy inference). Every parsing operation is implemented directly
in Python, making it impossible to support JS/TS (or any other language) without either:

- Rewriting each language's parser in Python, or
- Embedding a polyglot runtime inside the backend

Neither scales.

## Goal

Extract all **language-specific** parsing logic into standalone **language drivers** that run
as separate processes and communicate with the backend over a standardized protocol
(JSON-RPC 2.0 over HTTP).

After the migration:

```
┌─────────────────────────┐         JSON-RPC / HTTP        ┌────────────────────────┐
│     Backend (Python)    │ ◄──────────────────────────────►│   Python Driver        │
│                         │                                 │   (parso, libcst, jedi)│
│  - Orchestration        │         JSON-RPC / HTTP        ├────────────────────────┤
│  - File scanning        │ ◄──────────────────────────────►│   JS/TS Driver (future)│
│  - Change detection     │                                 │   (bun, ts-morph)      │
│  - DB sync              │                                 └────────────────────────┘
│  - Call graph diffing   │
│  - Socket/progress      │
└─────────────────────────┘
```

The backend becomes a **language-agnostic orchestrator** that:
1. Discovers files and detects changes (file system level)
2. Asks the appropriate driver to parse, resolve MRO, resolve calls
3. Stores results in a **unified model** (same DB schema for all languages)

## Non-Goals

- **No new features.** Parsing output must be identical before and after.
- **No bug fixes** in existing logic (visitor.py is broken — leave it).
- **No JS/TS driver implementation** yet (just the architecture to support it).
- **No changes to DB model** (`core/model/nodes.py`, `core/model/schemas/`).
- **No changes to watcher, sandbox, socket, or API contracts.**
- **No changes to how the frontend consumes data.**

## Constraints

- The migration must be **testable incrementally** — each phase should produce
  identical output compared to the previous phase.
- The unified model already exists: `name`, `qname`, `position`, `type` (func/class/call).
  Drivers just need to return data in this shape.
- ID injection must remain **language-driver controlled** (Python uses docstrings,
  JS/TS will use something else). The backend doesn't care how IDs are managed.

## Guiding Principle

> **Same behavior, different boundary.**
>
> Every parsing result should be byte-for-byte identical before and after the migration.
> The only change is *where* the code runs and *how* it communicates.
