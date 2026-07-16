# Frontend 01 — Tool Faces and the Run Checklist

*(Rewritten 2026-07-16 against the shipped frontendv2 redesign —
plan/agent-v2/frontendv2, implemented in `features/Dashboard/features/Agent/`.
The original version of this doc targeted v1 concepts that no longer exist:
there is no `chat/artifacts/registry.ts` and no generic `ConfirmCard`.)*

v3's frontend work, in the redesign's terms: **flip two registry flags, add two
tool faces, build one checklist renderer both faces share.** If it takes more
than that, the redesign's registry design failed its test — same law as the
backend's "adding a tool = a spec + a module".

## Shipping a v3 tool through the redesign (the contract)

| Step | File | Change |
|---|---|---|
| 1 | `tools/registry.ts` | `describe` / `document`: `status: "coming-soon"` → `"available"`. The picker's `Soon` pill disappears, the row becomes selectable, `toolHint` starts carrying it — zero picker code changes. |
| 2 | `tool/faces/registry.tsx` | one `TOOL_FACES` entry per tool: `ConfigForm` + `DoneView` (+ `RunningView`, the one shell extension — below). |
| 3 | — | everything else (badge, card shell, decision flow, progress part) already handles any tool. |

**Wire-id alignment (do this before Phase A).** The frontend `ToolId` is
`"describe"` / `"document"`; the backend tools are `describe_nodes` /
`document_nodes`. `TOOL_FACES` and the tool part's tool name are keyed by the
**wire** name (walkthrough happens to match; the v3 tools don't). Decision:
add `wireId` to `ToolInfo` (`describe` → `"describe_nodes"`), key `TOOL_FACES`
by `wireId`, and send `wireId` as the `toolHint`. One field, no renames, no
ambiguity about which string travels.

## The checklist renderer (one component, both tools)

The artifact renderer for `render: "run_checklist"` — a projection of
`RunItem` states from the `tool_run/<id>` mirror (shared/02).

```
┌ ⚙ Describe nodes ─────────────────────── running ┐
│ ██████████████░░░░░░  validate_card (14/32)      │
│                                                  │
│  ✓ validate_card      Checks card fields before… │  ← preview = sentence 1
│  ✓ send_receipt       Emails the receipt after…  │
│  ✧ charge             writing…                   │  ← shimmer
│  ○ refund             already described          │  ← skipped_existing, muted
│  ⚠ _retry_backoff     failed validation          │  ← expandable error
│  · PaymentService     pending                    │
│  · payments/          pending                    │
│                                                  │
│  leaves first — parents are summarized last  ⓘ   │
└──────────────────────────────────────────────────┘
```

**Where it mounts.** Inside the tool card body — not as a separate thread
artifact. The shipped pattern for artifact-backed faces is the walkthrough's:
the face reads its mirror doc and seeds it on reload via a bridge hook.
The checklist copies it exactly:

- `tool/faces/shared/RunChecklist.tsx` — renders from a `useMirrorStore`
  selector (`selectToolRun(docId)`); doc id comes off the tool part.
- `useToolRunBridge(doc)` — clone of `useWalkthroughBridge`: when the mirror is
  cold (reload), seed from `getArtifact` (`stream/source.ts`). No new stream
  logic; the mirror already applies the patches.

**The one shell extension: `RunningView`.** frontendv2/03 ruled that running
bodies are shared (`ToolProgress`) and tools don't customize them. v3 is the
carve-out that rule anticipated: for run tools the checklist **is** the
progress display, and it must be visible *while the run spends* — that's the
whole live-quality-window argument (shared/02). So `ToolFace` gains an
optional `RunningView?: ComponentType<…>`; `ToolCard` falls back to
`ToolProgress` when absent. Walkthrough is untouched; describe/document supply
`RunChecklist` (progress bar on top, list under it, per the sketch).
`DoneView` renders the same `RunChecklist` (now static) + summary + undo.

## Checklist decisions (unchanged in substance, restated in redesign terms)

- **Rows in plan order (post-order), indented by `level`.** The list visibly
  fills bottom-up — leaves tick before parents. That looks "backwards" exactly
  once; the footnote (ⓘ: "children are written first so each parent is
  summarized from fresh summaries") turns the surprise into the feature.
  Reordering rows to *look* natural would lie about what the tool does.
- **Visual idiom: the walkthrough `OutlineTree`.** Indented rows in a bordered
  inset list, mark glyph + label + mono meta — the checklist is its sibling,
  built from the same tokens (`--agent-bg-inset`, mono meta, accent marks).
  `writing` rows reuse `GeneratingShimmer` (already in
  `walkthrough/components/`).
- **States map 1:1 to `RunItem.state`**, colored by token, never by hex:
  pending `·` faint · writing `✧` shimmer · written `✓` accent · skipped `○`
  muted + "already described" · failed `⚠` warn (click expands the validator
  message — honest, specific, quietly educational).
- **Previews are the product.** Describe rows show the written first sentence;
  document rows the doc title. The user judges quality live and can Stop at
  item 5 instead of item 50. Without previews this is just a progress bar and
  bad output is discovered after the bill.
- **Row click focuses the node on canvas** (the executor's `setCenter`
  affordance). Document rows gain a second affordance once written: open the
  doc in the existing viewer — the finished checklist doubles as the subtree's
  table of contents.
- **Completed summary line**: "28 written · 3 skipped · 1 failed ⚠" — plus,
  on describe runs, the loop-closing nudge: *"child lists in future tours now
  use these."*

## Config forms (replaces "the v2 ConfirmCard renders knobs generically")

There is no generic confirm card in the shipped panel — each tool's
`awaiting_confirmation` body is its `ConfigForm` face (estimate + knobs in,
draft state local, decision out through `useDecision`). The v3 forms, built
from `tool/controls/` atoms:

- **describe** — `DepthSlider` (1..subtree max from `knobs`) · skip line from
  the estimate ("32 nodes · 20 calls · **12 already described — skipped**") ·
  `overwrite` toggle, off by default, with its one-line consequence ("replaces
  agent-written text only; human text is never touched"). Needs one new atom:
  `controls/Toggle.tsx` (Radix Switch skinned to the tokens).
- **document** — `DepthSlider` · **intent textarea** exactly as the mock/
  frontendv2-03 specced it (label `Intent`, hint `suggested — edit or approve`,
  inset field, accent focus, prefilled with the agent's distilled intent —
  this ships here, since intent is a document-tool arg) · `overwrite` toggle ·
  the `undescribed_children` hint when knobs carry it ("14 children have no
  descriptions — run describe first for a better doc"). Text only, no
  auto-chaining; the user can decline, cancel, or go run describe.

**Done faces vs the mock.** frontendv2's mock drew single-node done faces
(describe = result text box, document = file chip + Open). For these *run*
tools the checklist + summary supersedes both — the mock faces assumed one
node; the tools ship subtree-shaped. The file-chip affordance survives as the
per-row open-doc link. (frontendv2/03 carries a pointer here so the specs
don't compete.)

## Undo (Phase C, shared/03)

A completed, non-reverted run's `DoneView` shows **Undo this run** behind an
AlertDialog ("reverts 28 descriptions written by this run; nodes edited since
will be left alone"). Reverted runs render dimmed with a `reverted` badge —
the checklist stays in the transcript as the record of what happened and was
undone, listing any edited-since nodes the revert skipped.

## Cost

Two registry flag flips + one `wireId` field · two `TOOL_FACES` entries · one
`RunChecklist` + one `useToolRunBridge` · one optional `RunningView` seam in
`ToolCard` · one `Toggle` control atom. No new stream logic, no new part
types, no walkthrough-side changes — the redesign's registry design,
demonstrated a second time.
