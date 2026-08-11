# Task Management v2 — Mock-Fidelity Rebuild

**Source of truth: `~/Downloads/taskmangment/V-NOC Tasks.dc.html`** (the
approved Claude-Design mock; `vnoc-tasks-standalone-src.dc.html` is
byte-identical, the print variant has the same six screens). Every value in
these docs — colors, sizes, spacing, behavior — is extracted from that file's
markup and its inline JS (`INITIAL_TASKS`, `cardVM`, `detailVM`,
`renderVals`). Where a doc cites a line, it cites that file.

v1 shipped a UI that neither matches the design nor implements its content:
the detail panel has no title editing, no description, no created/updated,
no labels, no subtask checkboxes, no dependencies — and what it does render
uses generic Tailwind grays instead of the mock's palette. v2 is the
corrective: **build what the mock shows, styled how the mock styles it.**

## Ground rules

1. **The mock wins.** Where these docs and `../0*.md` (v1 plan) disagree,
   the mock is right. The known reversals are listed below — they are
   deliberate, not oversights.
2. **Exact tokens, not approximations.** All colors/sizes go through
   `Tasks/theme.ts` (01). No `text-muted-foreground` where the mock says
   `#8b919d`. JetBrains Mono is part of the design language — keys, counts,
   qnames, statuses, timestamps are mono; titles and prose are not.
3. **Behavior comes from the mock's JS.** The mock is interactive; its
   handlers define the interaction contract (drag/drop, popover open/close,
   subtask toggle, panel navigation). Docs quote the semantics, the build
   wires them to the real API (which already serves every field the mock
   displays — see 05).
4. **The behavior bugs come first.** None of this renders correctly while
   per-task routes 404 and the board GET is browser-cached — land
   `../fixes/01` and `../fixes/02` before or with v2.

## Deliberate v1 → v2 reversals (the mock decides)

| v1 plan said | v2 (mock) says | Consequence |
|---|---|---|
| No backlog column on the kanban; List view owns backlog | **Board renders all 5 columns**: `Backlog · To do · In progress · In review · Done` (mock `COLUMNS`) | The List view and the board-side `Backlog n` link drop out of v2 scope; backlog is a drag target like any column |
| One search box absorbing the anchored-node filter | **Two inputs**, as designed: the type segmented control + a mono `Filter by anchored node…  e.g. main.dd` input | 02 specs both; the general search box can return later without changing the bar's shape |
| Scope pill (This node · This tab · All) | Not in the mock | Out of v2; the seam in the query key survives |
| Popover with link-toggles, attach search, drag-transfer | **Read-only popover**: task rows only, click opens detail (mock `popoverTasks`) | Linking surfaces stay in the modal + detail panel for now |
| Detail STATUS/PRIORITY as dropdowns | **Read-only field tiles** in the 2×2 grid | Status changes via board drag (all 5 columns are on the board now) and the subtask checkbox; editing-in-panel is a marked enhancement, not v2 scope |

Everything else in the v1 plan (data model, API, anchors, hot rule,
right-slot exclusivity) stands unchanged underneath this UI.

## How to implement (the path for the executing model)

This folder is written to be executed by a smaller model. Read in this
order, and treat the algorithms as instructions, not suggestions:

1. **[00-vision-and-architecture.md](00-vision-and-architecture.md)** —
   the map: system shape, the ten invariants (L1–L10), the build sequence
   B1–B3 / F1–F5. Every later doc assumes you hold these.
2. **[08-backend-spec.md](08-backend-spec.md)** — backend, in section
   order, each with a test gate. The tricky algorithms (anchor add /
   remove / **move-transfer with merge degeneration**, call resolution,
   cycle-check direction with a worked example, delete ordering, schema
   migration) are written out step-by-step — **do not improvise them**.
3. **[09-frontend-spec.md](09-frontend-spec.md)** — frontend wiring order:
   foundation (tokens, api client, error toasts) → mutation recipes
   (optimistic shapes, and where NOT to be optimistic) → board → detail
   panel → create flow → canvas. Ends with a hand-run checklist.
4. **01–07** are the reference specs you consult while executing: exact
   pixels/colors (01–04), interaction contracts (07), data-model rationale
   (06). When 08/09 cite a section, that section is the truth.

## Files

| Doc | Covers | Mock region |
|---|---|---|
| [00-vision-and-architecture.md](00-vision-and-architecture.md) | Vision, system shape, invariants L1–L10, build sequence | — |
| [01-design-tokens.md](01-design-tokens.md) | The full palette, type ramp, radii, chips, icons, keyframes → `Tasks/theme.ts` | `TYPES`, `PRIO`, `KIND_ICON`, `COLUMNS`, inline styles throughout |
| [02-board.md](02-board.md) | Filter bar, 5 columns, task card anatomy + every state, drag & drop | "Tasks board" screen |
| [03-detail-panel.md](03-detail-panel.md) | **The panel, all 9 sections** — title input, fields grid, labels, description, anchors, subtasks, dependencies, activity | "Task detail panel" screen + `detailVM()` |
| [04-canvas-and-sidebar.md](04-canvas-and-sidebar.md) | Node badge/glow/focus, task popover, sidebar tree badges, tab-bar count | "Canvas", "Node task popover", "Sidebar" screens |
| [05-gap-closure.md](05-gap-closure.md) | Shipped-component → v2 change list, data availability audit, build order | — |
| [06-subtasks-as-self-references.md](06-subtasks-as-self-references.md) | Data-model correction: `subtasks`/`blocked_by` become real `Set["TaskSchema"]` self-links (house pattern), replacing the `*_ids_json` blobs; anchors stay soft by design | — |
| [07-subtasks-and-node-selection.md](07-subtasks-and-node-selection.md) | Subtask add/link/unlink interactions (search-or-create input, DAG entry, cycle toasts) · the anchor node picker · **the call rule: calls resolve to their target function/class, never anchored directly** | — |
| [08-backend-spec.md](08-backend-spec.md) | Backend build order: query-param routes, cache removal, self-link schema + migration, the anchor algorithms (add/remove/move), cycle check, delete ordering, test gates | — |
| [09-frontend-spec.md](09-frontend-spec.md) | Frontend build order: theme/api/toast foundation, optimistic-mutation recipes, board & panel rebuild wiring, create flow, canvas, done-checklist | — |

## Definition of done

Put the mock and the app side by side showing VN-9 (*Refactor main module*):
same panel width (384px), same section order, same chip colors, same mono
usage, same hover/focus treatments. A reviewer who can tell which is which
in under five seconds names what differs, and that's the bug list.
