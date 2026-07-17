# Grouper 04 — Frontend: ConfigForm, ReviewView, DoneView

Written against the shipped frontendv2 panel (`features/Dashboard/features/
Agent/`). The grouper's frontend cost follows the redesign's contract
(agent-v3 frontend/01 set the precedent): registry flip + faces. The only
genuinely new surface is the **ReviewView** — the editable proposal — and the
one shell extension it rides on.

## Registry changes

- `tools/registry.ts`: `group` → `status: "available"`, `wireId:
  "group_children"` (the frontend id stays `group`; faces and `toolHint` key
  by `wireId` — the alignment rule from agent-v3 frontend/01 applies here
  verbatim).
- `tool/faces/registry.tsx`: `ToolFace` gains `ReviewView?:
  ComponentType<ToolReviewProps>` — the gate-2 sibling of agent-v3's
  `RunningView` carve-out. `ToolCard` renders it when the part state is
  `awaiting_review`; tools without one can't reach that state
  (`review="never"`), so no fallback face is needed beyond a defensive
  generic message.
- Badge: **no new color.** `awaiting_review` reuses the warn variant — both
  waiting states mean "the run is paused on you" and amber already means
  that. The *label* differs: `needs approval` vs `review groups`. (Token
  discipline from frontendv2/06: new colors require a design-mock update
  first; a second waiting-hue isn't worth reopening the palette.)
- The pending-card border treatment (`#3a3320` amber tint) applies to
  `awaiting_review` too — same signal, same styling rule.

## ConfigForm (gate 1) — the mock's face, plus one field

The mock already drew this (frontendv2/03: three steppers in a 3-col grid):

- `Stepper` ×3 — MIN CHILDREN (2–10, default 4) · MIN GROUPS (2–`max`) ·
  MAX GROUPS (`min`–12, default 6). Cross-constraints in the tested pure
  reducer the redesign already specced; prefilled from the estimate's knobs.
- **Category** (new, not in the mock): one inset text input under the
  steppers, label `Group by`, placeholder `optional — e.g. "lifecycle stage";
  leave empty and the agent will suggest one`. Maps to the `category` arg.
  Prefilled when the agent extracted a dimension from the user's message.
- The `undescribed` hint line when knobs carry it: "9 of 14 children have no
  descriptions — run describe first for better groups" (text, faint, no
  button — same as document's).
- Actions: Cancel / **Create groups** (the registry `runLabel`).

## ReviewView (gate 2) — the new surface

Reads the `group_proposal/<run_id>` mirror doc (same `useMirrorStore` +
seed-on-reload bridge pattern as walkthrough/checklist — one
`useProposalBridge(doc)` clone). All edits live in a **local draft** copied
from the doc on mount; nothing leaves the component until Approve. Layout,
top to bottom:

```
GROUPED BY                                            ← section label, faint
┌────────────────────────────────────────────────┐
│ Grouped by pipeline stage: building, submitting │   ← dimension, editable
│ and reconciling charges.                        │     (inset textarea, 2 rows,
└────────────────────────────────────────────────┘      accent focus — the
                                                        intent-field idiom)
GROUPS · 3 of 2–6                                     ← live count vs knobs
┌ ▦ Charge flow ─────────────────────── 6 · ⋯ ┐
│  [charge.py ×] [submit.py ×] [retry.py ×] …  │      ← member chips
│  Builds and submits charge requests.         │      ← group description, editable
└──────────────────────────────────────────────┘
┌ ▦ Reconciliation ──────────────────── 4 · ⋯ ┐
│  …                                           │
└──────────────────────────────────────────────┘

UNGROUPED · 2
  [conftest.py ▾]  test scaffolding, not pipeline code
  [legacy.py ▾]    scheduled for deletion per its docs
                                                      ← reason lines, faint
┌ validator error line(s), quiet-red, when present ┐

            Cancel                 ✓ Approve & create
```

Interaction decisions:

- **Group name**: click-to-edit inline input (the canvas-label constraint —
  ≤30 chars — enforced live). **Group description**: one-line inset input
  under the chips.
- **Moving a member**: every chip gets a Radix DropdownMenu (the `⋯` /
  chip-click): "Move to → [other groups] · Ungroup". Ungrouped chips get the
  mirror menu ("Add to → …"). **No drag-and-drop in v1** — the menu is
  keyboard-accessible for free, works at 60 children, and ships a phase
  earlier; drag is polish the seam allows later.
- **Dissolve group** (in the group's `⋯` menu): members drop to the
  ungrouped section with reason `removed by you`. **New group**: a ghost
  "+ New group" card appears while `len(groups) < max_groups`.
- **Live validation** mirrors the backend laws (02) — count badge turns warn
  outside `min–max`, a 1-member group shows its row-level warning, Approve
  disables with the reason as its tooltip. Advisory only: Approve sends the
  full draft; a backend 422's sentences render in the quiet-red line and the
  card stays editable (03's resume semantics).
- **Approve** → `useDecision` with `{kind: "review", action: "approve",
  proposal: draft}`. **Cancel** → `{action: "cancel"}` behind no dialog
  (nothing is written yet; cancel is free — the AlertDialog is for undo,
  which destroys things).

Component layout (per frontendv2/01 conventions — presentation components
take props only):

```
tool/faces/group/
├── ConfigForm.tsx        steppers + category + hint
├── ReviewView.tsx        wiring: mirror doc → draft state → decision
├── ReviewDimension.tsx   the editable explanation
├── ReviewGroupCard.tsx   name/description/chips/menus for one group
├── ReviewUngrouped.tsx   remainder + reasons
├── DoneView.tsx          pills + dimension + undo (G4)
└── draft.ts              pure draft reducer: move/rename/dissolve/add
                          + client-side validator mirror — vitest here
```

`draft.ts` is where the tests live: every menu action is a pure function on
the draft, and the validator mirror shares its fixture table with the
backend's (same JSON fixtures, two runners — they cannot drift silently).

## DoneView

The mock's face, made real: wrap of pill chips (grid glyph + name + mono
count) + the dimension line under them ("Grouped by pipeline stage") + the
footer `approved · 3 groups created` — or `edited, then approved` when
`edited_by_user` (the honesty stamp from 03). Ungrouped remainder listed
faintly. G4 adds **Undo this run** behind the AlertDialog (05). Row click on
a pill focuses the group's box on canvas (the `setCenter` affordance).

## Build steps

1. `ToolFace.ReviewView` slot + `awaiting_review` badge label + card-border
   rule — shell only, fixture part driving the state.
2. `draft.ts` reducer + validator mirror + shared fixtures (pure, tested,
   no UI).
3. ConfigForm (steppers exist; add category + hint).
4. ReviewView components against a fixture proposal doc; then against the
   real G2 backend (approve/cancel/422 paths).
5. DoneView + registry flip (`group` available) — last, so the picker only
   offers what works end to end.
