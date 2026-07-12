# 05 — Edge Cases

Every "what if" gets one deterministic answer. The theme: the tour **borrows** the
user's workspace and must always give it back.

## View snapshot and restore

At `play()`, before the first step executes, snapshot the tour tab's view state:

```typescript
interface SavedView {
  tabId: string;
  focusStack: AnyNodeTree[];       // useProjectStore.focusStack[tabId]
  selectedNode: AnyNodeTree | null;
  expandedNodeIds: string[];
  viewport: { x: number; y: number; zoom: number };   // reactFlow.getViewport()
}
```

`exit()` restores all of it (clearFocus → pushFocusBulk(saved) → set selection →
restore expansions → setViewport) and clears decorations. This single mechanism
answers half the table below.

## The table

| # | Situation | Behavior |
|---|---|---|
| 1 | **Play clicked while another tab is active** | The tour is bound to `tabId` (where it was started). `play()` calls `setActiveTabId(tourTabId)` first. No cross-tab playing: one tour, one tab. |
| 2 | **Tour tab's main view isn't the canvas** (Code/Docs/Sandbox view open) | `play()` also switches the tab's main view to canvas via the existing view-mode state, and restores the previous view on `exit()` (part of `SavedView`). |
| 3 | **User is focused/zoomed on an unrelated node** | Normal case, not an error: `ensureOnCanvas` replaces the focus stack with the step's lineage; the snapshot restores the user's focus on exit. |
| 4 | **Step's node not loaded (lazy children / pagination)** | The injection query (04): `getLineage` → `resolveLineageFromPath` (pages through missing ancestors) → `pushFocusBulk` + `expandNodesBulk`. Invisible to the user beyond a brief spinner on the StepCard. |
| 5 | **Injection fails** (node deleted since generation, network error) | Toast "couldn't reach `name`", ⚠ on the outline row, cursor stays. Next skips past. Never abort the tour. |
| 6 | **User pans/zooms mid-step** | `userInteracted` flag: executor stops re-centering until the next step. The tour never fights the mouse. |
| 7 | **User clicks/selects other nodes mid-tour** | Allowed. The next executed step re-selects. If it opened a call-portal tab, it stays — user action, user's tab. |
| 8 | **Next pressed past the last generated step** (play-while-generating) | Shimmer in the StepCard body; auto-advance when the text patch lands. If `end(error)` arrives instead: ⚠ row + card message. |
| 9 | **Stream drops mid-generation** | `end` never came: phase → `error`, generated steps stay playable, banner offers "Regenerate" (full re-run — no partial resume in MVP; `seq` exists for later). |
| 10 | **Tour tab is closed during a tour** | Tab removal already cleans per-tab state; a store subscription on `useTabStore.tabs` calls `discard()` when `tourTabId` disappears. |
| 11 | **Project switched / route change** | Same subscription pattern on project id → `discard()`. |
| 12 | **Editor not ready when highlight fires** (Monaco mounting, code query in flight) | Highlight effect waits on `editorReady && codeLoaded`; 5 s timeout → degrade to text-only (⚠), don't block the step. |
| 13 | **Code query returns different line span than the fixture/backend expected** (stale graph vs. source) | Clamp the range to the editor's line count, flag ⚠. (Proper fix is commit-pinned code loading — post-MVP, parent 04.) |
| 14 | **Contextual stop whose node is a call in an unexpanded parent** | Same as #4 — lineage expansion materializes the call node like any other. |
| 15 | **Generate clicked while a tour exists** | Confirm dialog → `discard()` → new `start()`. One tour at a time. |
| 16 | **Esc pressed while generating** | Exits *playback* only; generation continues in the background (phase back to `generating`), outline keeps filling. |
| 17 | **Arrow keys while typing elsewhere** | Key handlers are registered only in `phase === "playing"` and skip when focus is in an input/editor. |
| 18 | **Same node appears twice on canvas** (e.g. call portal duplicated it in another tab) | Executor only ever addresses nodes in `tourTabId`'s canvas; other tabs are out of scope by construction. |

## What we deliberately do NOT handle in MVP

- Resuming a broken stream at `seq` (numbering is in place; logic is later).
- Playing a session against a *changed* graph with full fidelity (needs commit-pinned
  node/code loading — parent plan 04; frontend behavior today is #5/#13 degradation).
- Multi-tab or split-screen tours.
- Restoring canvas viewport perfectly when the window was resized mid-tour (restore
  is best-effort `setViewport`).

Each of these degrades visibly rather than silently — the contract from 00 holds.
