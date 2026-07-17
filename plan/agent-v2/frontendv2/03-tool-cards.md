# Frontend v2 — 03: The Tool Card

The centerpiece of the design. One shell, one badge system, and per-tool
**faces** (config form + done view) behind a registry. The mock draws all four
tools' faces; this doc specs all four, but only walkthrough's is *built* until
its tool exists (README decision #5).

## State model — mock names vs wire truth

The card renders the tool part's wire state (data-model/01). The mock's fixture
states map onto it; the wire has one state the mock lacks (error), and the mock
has one the wire expresses as a decision (cancelled).

| Wire state | Mock name | Card face |
|---|---|---|
| `pending` | — (instant in mock) | header only, badge "queued", body collapsed |
| `awaiting_confirmation` | `pending` / "needs approval" | config form + Cancel/Run |
| `running` | `running` | striped progress bar |
| `completed` | `done` | per-tool done view |
| `error` | — | quiet-red badge + failure line |
| cancelled (user declined) | `cancelled` | gray badge, collapsed |

## Shell (`ToolCard.tsx`)

Radix Collapsible. From the mock:

- Card: `--agent-bg-tool`, radius card, 1px border — `--agent-border` normally,
  the amber-tinted `#3a3320` **only** while `awaiting_confirmation` (the card
  itself signals "waiting on you").
- Header row (whole row is the toggle button, hover `--agent-bg-raised`):
  - **Icon tile** 26px, radius 7, accent-tinted bg/border, accent-text glyph.
    Glyph comes from the tool registry (04) — play triangle (walkthrough),
    text lines (describe), document (document), four squares (group).
  - **Name** 13px/600 over **meta** mono 10.5px faint, single line, ellipsized.
    Meta = short conversation hash + the tool's human estimate line
    (`372f9c6e · 6 stops · ~9 LLM calls`). The estimate numbers come from the
    backend estimate payload, not a frontend table (the mock's `TOOLS[k].meta`
    is fixture data).
  - **Badge** (`ToolBadge`, cva) + chevron (rotates 180° when open).
- Expanded body: border-top, 14px padding, 14px gap.

Badge variants (pill, 10px/650):

| Variant | Colors (tokens) | Extra |
|---|---|---|
| queued | muted on raised | |
| needs approval | warn on warn-bg/warn-border | |
| running | accent-text on accent-bg | pulse animation (static when reduced-motion) |
| done | accent-text on accent-bg | |
| error | danger on danger tints | |
| cancelled | muted on raised | |

Expansion default: `awaiting_confirmation` and `error` open; `running` open;
`completed` collapsed **except** walkthrough (its done view is the payoff);
cancelled collapsed. User toggle always wins after first interaction (local
state).

## Face registry (`tool/faces/registry.tsx`)

```ts
interface ToolFace {
  icon: LucideOrSvg;
  ConfigForm: FC<{ estimate; draft; onChange }>;   // awaiting_confirmation body
  DoneView: FC<{ part }>;                          // completed body
}
registry: Record<ToolId, ToolFace>
```

Running/error/cancelled bodies are shared shell components (`ToolProgress`, an
error line) — tools don't customize them. A tool part whose id has no face
renders a generic "tool ran" face — the frontend never crashes on an unknown
tool.

## Confirmation face (`awaiting_confirmation`)

Layout per the mock, top to bottom: controls → note → actions.

**Draft state.** The estimate payload carries the agent's suggested config
(depth, detail, intent…). The form copies it into local draft state on mount;
edits touch only the draft; **Run** posts the draft through `useDecision`
(approve + config), **Cancel** posts a reject. No optimistic state transitions —
the card changes state when the stream says so (single source of truth held by
the backend).

**Controls, per tool:**

- **All tools — `DepthSlider`.** Radix slider, 1..`realMax` where `realMax` is
  the WOQL-probed subtree max from the estimate (mock's `treeMax`). Right-aligned
  mono label: `2 (this tree: max 4)`. Accent thumb (16px, inset border per mock).
- **Walkthrough — `Segmented` detail.** Quick / Normal / Detailed on the inset
  track (radius field, 3px padding); selected segment raised + bright. Maps to
  the walkthrough tool's verbosity hint.
- **Document (spec only, ships with agent-v3) — intent textarea.** Label row
  `Intent` + right hint `suggested — edit or approve` (10.5px faint). Inset
  textarea, 3 rows, resize-vertical, accent focus border. Prefilled with the
  agent's distilled intent.
- **Group (spec only) — three `Stepper`s** in a 3-col grid: MIN GROUPS /
  MAX GROUPS / MIN CHILDREN. Cross-constraints live in a pure reducer (tested):
  minGroups ≤ maxGroups always; bounds 1–12 / 2–10 per the mock.

**Note + actions row.** Faint 11px explanation — improve the mock's static
sentence: state *why* approval is needed, from the estimate ("~9 LLM calls is
above the auto-run limit"). Right: `Cancel` (ghost) and the primary Run button
(accent-btn, play glyph, per-tool label from the registry: "Run tour",
"Generate", "Generate doc", "Create groups").

## Running face

- 5px track (raised token), fill = accent 45° stripes sliding (mock's `barSlide`;
  static fill under reduced-motion).
- Mono 11px line: `3 / 9 steps · running…` — numerator/denominator/unit from
  the tool part's streamed progress fields, unit word from the registry
  (steps / calls / sections / passes).
- A stop affordance is *not* in the mock — add none here; run-level stop lives
  in the composer (04), which is the single place to cancel a turn.

## Done faces

**Walkthrough (`faces/walkthrough/DoneView.tsx`)** — the mock's richest view:
1. Full-width primary button `Play walkthrough` (play glyph) → mounts the
   existing player via the artifact bridge; label flips to `Exit playback`
   while `useWalkthroughStore` is active.
2. Centered faint `9 steps ready`.
3. `TOUR OUTLINE` section label, then the outline tree in a bordered rounded
   list: rows indented by depth (12/28/46px), mark glyphs ✓ (accent, has
   narration) / ● (faint dot) / ▸ (sub-item), label 12.5px/600 (12px/450 for
   subs), kind in mono parens, right-aligned `⇢ stop 3` links (accent-link)
   that jump playback to that stop. **Data**: the walkthrough artifact doc in
   the mirror store — the same doc the player consumes; the mock's `OUTLINE`
   array is its fixture stand-in. Reuse v1's flatten/selector logic (it moves
   with `walkthrough/store/`).
4. Faint footer over a top border: `approved · walkthrough created` — the
   decision + outcome, from the tool part.

**Describe (spec only).** Result text in an inset rounded box, 12.5px/1.6 body.

**Document (spec only).** File chip row: doc icon, mono filename, faint word
count, right `Open` link (accent-link, 600) → opens the doc in the existing
document surface.

**Group (spec only).** Wrap of pill chips: grid glyph + group name + mono count.

> **Superseded for describe/document (2026-07-16):** those two ship in agent-v3
> as subtree *run* tools, not single-node calls — their real faces (config
> forms with overwrite/intent, a live run checklist as RunningView/DoneView)
> are specced in `plan/agent-v3/frontend/01`. The mock's single-node done faces
> above stay as the visual reference only.
>
> **Superseded for group (2026-07-17):** the grouper ships as the first
> two-gate tool — its real faces (steppers + category at gate 1, an editable
> proposal `ReviewView` at gate 2, pills + dimension line when done) are
> specced in `plan/grouper/04`. The mock's steppers and pills remain its
> visual reference.

## Error face (not in the mock — designed here)

Failure is boring (README): badge `error` in the quiet danger tint; body is one
inset box with the failure summary the backend reports on the part (never a raw
traceback), collapsed details if the part carries them. The agent's follow-up
text ("the tour failed, but here's what I can tell you…") arrives as a normal
text part after the card — the card doesn't need to editorialize.

## Build steps for this doc

1. `ToolCard` shell + `ToolBadge` + expansion rules against a fixture part
   cycling states (storybook-style dev route or vitest + testing-library).
2. `ToolProgress` + shared error line.
3. Face registry + generic fallback face.
4. Walkthrough `ConfigForm` (DepthSlider + Segmented) wired: estimate in,
   decision out; verify against a real backend interrupt.
5. Walkthrough `DoneView` (outline tree + play bridge).
6. Cancelled + error paths end-to-end (kill the backend mid-run to see error).
