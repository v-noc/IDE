# Walkthrough Frontend — MVP Plan

> How the walkthrough player lands in the existing React frontend: what we reuse, what
> we build, how it runs on **mock patch-log JSON first** and swaps to the backend with
> a one-line change.

Parent plan: [`plan/walkthrough-agent/`](../README.md). Types and the wire protocol
come from [04-data-types.md](../04-data-types.md) — this folder is only about the
frontend.

## MVP stance (read this first)

1. **One new package: `fast-json-patch`.** The wire is NDJSON frames of JSON-Patch ops
   applied to a session mirror (the Eregna patcher pattern). Everything else is
   already installed: `@monaco-editor/react` (code view), `@xyflow/react` (canvas),
   `zustand` + `immer` (state), `@tanstack/react-query` (data), Radix UI, `zod`.
2. **Reuse the Agent feature shell.** `features/Dashboard/features/Agent/` already has
   a sidebar, overlay, toggle and bottom bar. The walkthrough becomes a sub-feature
   inside it. The existing timed `ReplayRunner` is a prototype for *later* auto-play —
   MVP does not touch or extend it.
3. **Click-through only.** A fixed step card with Next/Prev. No timers, no seek bar,
   no speed control. The line-anchored floating popup is deferred; MVP highlights
   lines in Monaco and shows the text in a fixed card.
4. **Mock-first by construction.** The player consumes a `WalkthroughSource` that
   yields frames. `MockSource` replays a recorded patch-log fixture with delays;
   `HttpSource` reads the real NDJSON stream. Components cannot tell them apart, so
   "swap to backend" means changing one provider, not touching components.
5. **No drag-and-drop yet.** The launcher uses the **currently selected node** ("Use
   selected: `charge()`"). Drag-drop is polish on top of a working selection system.

## Files

| # | File | Answers |
|---|------|---------|
| 00 | [00-scope.md](00-scope.md) | What MVP builds, reuses, and explicitly skips. |
| 01 | [01-folder-structure.md](01-folder-structure.md) | Where every file goes; the few files touched outside the feature. |
| 02 | [02-wire-and-mock.md](02-wire-and-mock.md) | Patch frames, the source interface, fixtures, the backend swap. |
| 03 | [03-store-and-player.md](03-store-and-player.md) | Store, flattening, and every way the user moves through steps. |
| 04 | [04-canvas-integration.md](04-canvas-integration.md) | The three actions on the real canvas; the node-injection query; Monaco highlight. |
| 05 | [05-edge-cases.md](05-edge-cases.md) | Wrong tab, wrong focus, unloaded (lazy/paginated) nodes, and friends. |
| 06 | [06-build-order.md](06-build-order.md) | Build sequence with a mock checkpoint at every stage. |
