# Walkthrough Fixes — Review Findings and Fix Guide

> Written after reviewing the first implementation (commits `b0ffb3cd` frontend,
> `30049c3a` backend, plus uncommitted backend files). Each doc is one fix area with
> exact file paths, what is wrong, what "fixed" looks like, and how to verify.

## Who this is for (read before coding)

This guide will be executed by a **small model**. Follow these working rules:

1. **Never trust this guide's line numbers or the code you remember.** Files change.
   Before every edit: OPEN the file, FIND the code by searching for the quoted
   snippet, and confirm it looks like what the doc describes. If it doesn't match,
   stop and re-read the surrounding code before changing anything.
2. **One fix doc at a time, in order.** Finish, verify, then move on. Do not batch
   edits across docs.
3. **Verify by running, not by reading.** Every doc ends with a "Prove it" section —
   run those exact commands. A fix without a green check is not done.
4. **Do not refactor beyond what the doc says.** If you see something else that looks
   wrong, write it down at the bottom of this README under "Parking lot" — do not fix
   it inline.
5. Backend tests: `cd src/backend && uv run pytest tests/unit/walkthrough -q`
   Frontend tests: `cd src/frontend && yarn test`

## Fix order

| # | Doc | What | Why this order |
|---|-----|------|----------------|
| 01 | [01-mock-real-node-data.md](01-mock-real-node-data.md) | Mock mode generates the tour from the **real selected node**, lorem narration only | The demo is the point right now; everything else is verified through it |
| 02 | [02-ui-play-flow-and-step-card.md](02-ui-play-flow-and-step-card.md) | Clear Play/Resume flow, step card sizing and placement | Second half of the demo complaint |
| 03 | [03-frontend-correctness.md](03-frontend-correctness.md) | Contract and playback bugs found in review (some break the tour outright) | Needed before the demo is trustworthy |
| 04 | [04-backend-correctness.md](04-backend-correctness.md) | Traversal / retry / call-code bugs — includes the 3 already-failing tests | Backend is not demo-blocking (mock mode), but these are real bugs with tests waiting |
| 05 | [05-verification-checklist.md](05-verification-checklist.md) | The full manual pass after 01–04 | Final gate for round 1 |
| 06 | [06-expand-pagination-bug.md](06-expand-pagination-bug.md) | **Canvas bug**: lazy children invisible until collapse + re-expand (missing memo dep + unstable map identity) | Round 2 — land FIRST, 07/08 depend on it |
| 07 | [07-node-anchored-popover.md](07-node-anchored-popover.md) | Popover anchored to the node's left via ReactFlow `NodeToolbar`, tracks pan/zoom, renders above everything; bottom card becomes a slim pill | Round 2 |
| 08 | [08-expand-upfront-and-camera.md](08-expand-upfront-and-camera.md) | Play pre-expands all stops; focus the tour root once, then slide at the user's zoom; single camera driver; no portal-tab side effects | Round 2 — needs 06; Step C-1 corrected by 09 |
| 09 | [09-spotlight-not-reroot.md](09-spotlight-not-reroot.md) | **Regression fix**: playback re-roots the canvas per step (selection = layout root), hiding all other nodes. Root once at Play, secondary selection per step, driver.js-style CSS spotlight (dim others, never hide) | Round 3 — supersedes 08 Step C-1 |

## Current known state (measured, not assumed)

- Frontend: `yarn test` → 7 passed (2 files).
- Backend: `uv run pytest tests/unit/walkthrough -q` → **3 failed**, 11 passed:
  - `test_traversal.py::test_over_cap_flag` — over_cap can never become true (04-B2)
  - `test_traversal.py::test_recursion_is_contextual` — duplicate rule misses (04-B3)
  - `test_structured.py::test_structured_call_retries_then_succeeds` — retry state
    broken (04-B4)
- `import app.walkthrough.service` currently succeeds on this machine, **but**
  `pipeline.py` imports `app.walkthrough.context`, and there is no
  `app/walkthrough/context.py` in the working tree. Do not trust that import to keep
  working (fresh clone, other machine). 04-B1 removes the ambiguity.

## Round 2 notes (2026-07-08)

User-reported after the first demo, investigated and confirmed in code:

- The lazy-children bug (06) is real and pre-dates the walkthrough: the layout
  `useMemo` in `useEnhancedTreeLayout.tsx` reads `lazyChildrenByParentId` but does
  not list it as a dependency, and `CanvasView` rebuilds that map with an unstable
  identity every render. Fix = memoization correctness, explicitly **no new
  useEffect**.
- The "camera focuses every node / hard to tell where I am" feel has three stacked
  causes, all in 08: per-step re-centering at zoom 1, `CanvasView.centerOnTarget`
  double-driving the camera on every tour selection, and `handleNodeSelection`
  spawning portal tabs on call stops.
- `CanvasView.onMoveStart` already has the `if (!event) return` guard (03-F6) in the
  working tree — verify rather than re-apply.

## Parking lot

(Implementer: add anything suspicious you find but were not told to fix.)
