# 00 — Scope

What the frontend MVP builds, what it reuses from the existing codebase, and what it
deliberately skips. Everything below was checked against the code, not assumed.

## What already exists (reuse, don't rebuild)

| Existing thing | Where | Used for |
|---|---|---|
| Agent shell: sidebar, overlay, toggle button, bottom bar | `features/Dashboard/features/Agent/` | The walkthrough panel lives in this shell |
| Tab system with per-tab state | `useTabStore` (`tabs`, `activeTabId`, `handleNodeSelection`) | Tour is bound to one tab; play switches to it |
| Selection / focus / expansion per tab | `useProjectStore` slices (`selectionSlice`, `focusSlice`, `uiSlice`) | `select_node` and `show_code` actions |
| **Node injection query** | `codeApi.getLineage(projectKey, nodeId)` → `resolveLineageFromPath(...)` → `pushFocusBulk` + `expandNodesBulk` (see `useTabStore.handleNodeSelection`) | Getting a step's node onto the canvas when it isn't loaded — calls, lazy children, pagination |
| Lazy / paginated children | `service/codeDescendants` (`useLazyCodeChildren`, `getCodeDescendantsQueryOptions`), `lazy_child_ids` | Steps must not assume a node is materialized |
| Node rendering + code view | `EnhancedNode`, `NodeCodeView`, `useNodeCode` (react-query `useCode`), `CodeEditor` (`@monaco-editor/react`) | `highlight_lines` decorates this editor |
| Canvas | `CanvasView` (per `tabId`), ReactFlow instance | pan/zoom for `select_node` |
| Fixtures pattern | `Agent/fixtures/conversations.ts` | Walkthrough fixtures follow the same pattern |

## What MVP builds

1. **Walkthrough sub-feature** under the Agent feature: launcher panel (selected node
   + depth + estimate + Generate), tour outline, step card, and the walkthrough store.
2. **Patch-frame consumption**: `applyOps` on a session mirror (`fast-json-patch`),
   fed by a `WalkthroughSource` (mock or HTTP — see 02).
3. **Step executor**: turns the current `PlayerStep` into canvas effects — select,
   ensure-on-canvas (injection query), expand, Monaco line decorations.
4. **Monaco highlight mode** inside the existing `NodeCodeView`: decorations +
   dimming + reveal, driven by store state, removed cleanly on exit.
5. **Fixtures**: two recorded patch-log JSONs (small function; class with methods and
   a call to another file) + a dev switch to run on them.

## What MVP skips (and why it's safe to skip)

| Skipped | Why safe |
|---|---|
| Timed auto-play, seek bar, speed | `ReplayRunner` prototype already sketches it; click-through steps are the same data |
| Line-anchored floating popup (Monaco content widget) | Step card is fixed-position; anchoring is pure polish, no data change |
| Drag-and-drop node into chat | Launcher reads the selected node; selection already exists |
| Estimate endpoint UI states | Show numbers when the endpoint exists; mock shows fixture numbers |
| Commit-pinned replay UI ("recorded at abc123" banner) | Sessions carry `commit_id` from day one; the banner is a later `if` |
| Reconnect / resume via `seq` | Frames are numbered from day one; resume logic is later |
| Multiple concurrent tours | One tour; starting another confirms + discards |
| Free chat input | The Agent chat input renders disabled in walkthrough mode |

## The one behavioral contract

Everything in this folder serves a single sentence:

> Given a session mirror (from mock or backend), the player can always drive the
> canvas to the current step — selecting the node, getting it on screen even if it
> was never loaded, showing its code, and highlighting the block — or degrade
> visibly (⚠ + skip) when it can't.

Edge cases (05) are all instances of "or degrade visibly".
