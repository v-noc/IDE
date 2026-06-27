# V-NOC Documentation

This folder is the authoritative reference for V-NOC. It is organised **top-down**: from *why* the project exists to *how* every subsystem works. Each domain has its own file so you can read just the part you need.

## How to read this

- **First time here?** Read `01-vision.md` → `02-architecture.md` → `03-getting-started.md` in order.
- **Setting up a real project?** Jump to `04-creating-a-project.md`.
- **Extending the IDE?** `05-language-drivers.md` and `06-function-class-tracking.md` describe the extension points.
- **Operating the IDE day-to-day?** The `07-logs.md`, `08-playground.md`, `09-test-tracking.md`, and `10-version-control.md` files cover the canvas-side features.

## Index

| # | Document | Audience |
|---|---|---|
| 00 | [README](README.md) — this page | Everyone |
| 01 | [Vision](01-vision.md) | Everyone |
| 02 | [Architecture](02-architecture.md) | Contributors |
| 03 | [Getting Started](03-getting-started.md) | New users |
| 04 | [Creating a Project](04-creating-a-project.md) | New users |
| 05 | [Language Drivers](05-language-drivers.md) | Contributors |
| 06 | [Function & Class Tracking](06-function-class-tracking.md) | Contributors |
| 07 | [Logs](07-logs.md) | All users |
| 08 | [Playground](08-playground.md) | All users |
| 09 | [Test Tracking](09-test-tracking.md) | All users |
| 10 | [Version Control (TerminusDB)](10-version-control.md) | All users |
| 11 | [Makefile Reference](11-makefile-reference.md) | All users |

## Conventions used in this documentation

- Code paths are written from the repository root: `src/backend/app/main.py`.
- HTTP endpoints are written relative to the backend root: `POST /api/v1/projects/`.
- Default ports are referenced symbolically: `BACKEND_PORT`, `RPC_PORT`, `LSP_PY_PORT`, `LSP_TS_PORT`, `TERMINUS_PORT`. Their default values live in the [Makefile](../Makefile) and can be overridden inline.
- "**The graph**" always refers to the TerminusDB-backed knowledge graph of the active project.
