# Frontend 01 — The Run Checklist UI

The artifact renderer for `render: "run_checklist"` — one component serving both
v3 tools, mounted by the v2 artifact registry (`chat/artifacts/registry.ts`
gains one entry). It reads the `tool_run/<id>` mirror; everything below is a
projection of `RunItem` states.

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

## Decisions

- **Rows in plan order (post-order), children indented by `level`.** The list
  visibly fills bottom-up — leaves tick before their parents. That looks
  "backwards" exactly once, so the one-line footnote (ⓘ tooltip: "children are
  written first so each parent is summarized from fresh summaries") turns the
  surprise into the feature it is. Reordering rows top-down to *look* natural
  would lie about what the tool does.
- **Previews are the product.** For describe runs the row shows the written
  first sentence; for document runs, the doc title. The user watches quality
  live and can Stop a bad run at item 5 instead of item 50 — the checklist is
  the same live-eval mechanism as watching tour stops fill in.
- **States map 1:1 to `RunItem.state`** — pending `·`, writing `✧` (shimmer),
  written `✓`, skipped `○` + "already described", failed `⚠` (click expands the
  validator message — honest, specific, and quietly educational about what the
  validator wants).
- **Row click focuses the node on canvas** (the `setCenter` affordance every
  node reference already has). On document runs, a second affordance: open the
  written doc in the existing document viewer — the checklist doubles as the
  subtree's table of contents when the run completes.
- **Completed summary line**: "28 written · 3 skipped · 1 failed ⚠" +, for
  describe runs, the one nudge that closes the loop: *"child lists in future
  tours now use these."*

## Undo (Phase C, shared/03)

A completed (non-reverted) run shows **Undo this run** behind a confirmation
dialog ("reverts 28 descriptions written by this run; nodes edited since will
be left alone"). Reverted runs render dimmed with a `reverted` badge — the
checklist stays in the transcript as the record of what happened and was
undone. If the revert skipped edited-since nodes, they're listed on the card.

## Confirm-card extras for these tools

The v2 ConfirmCard renders `knobs` generically; v3 adds two:

- `overwrite` toggle — off by default, with the one-line consequence ("replaces
  agent-written text only; human text is never touched");
- the `undescribed_children` hint on document runs ("14 children have no
  descriptions — run describe first for a better doc") — text only, no
  auto-chaining; the user can decline, cancel, or go run describe.

## Cost

One renderer component, one registry entry, one store selector
(`selectToolRun(docId)`). No new stream logic (mirror already handles the doc),
no new part types, no walkthrough-side changes — which is the point of v2's
artifact design, demonstrated a second time.
