# Frontend v2 — 04: Composer and Tool Picker

The bottom of the panel: where text, an attached node, a tool hint, and an
effort setting become one message. Also home of this build's product rule:
**all tools visible, only walkthrough enabled.**

## The tool registry (`tools/registry.ts`)

One module owns the tool list; the picker, the card faces (03), and any future
surface enumerate it — nobody hardcodes a tool name twice.

```ts
type ToolStatus = 'available' | 'coming-soon';

interface ToolInfo {
  id: 'walkthrough' | 'describe' | 'document' | 'group';
  name: string;      // "Code walkthrough"
  short: string;     // "Walkthrough" — picker button label
  desc: string;      // "Guided step-by-step tour of a node"
  runLabel: string;  // "Run tour" (03 uses this)
  unit: string;      // "steps" (03 progress line)
  icon: ...;
  status: ToolStatus;
}
```

Ship values (names/descs verbatim from the mock):

| id | name | desc | status |
|---|---|---|---|
| walkthrough | Code walkthrough | Guided step-by-step tour of a node | **available** |
| describe | Description generator | Concise description of a node | coming-soon |
| document | Document generator | Full document, with editable intent | coming-soon |
| group | Grouper | Organize children into groups | coming-soon |

When agent-v3 ships a tool, its flag flips and its face (03) gets built — the
picker, badges, and card shell need zero changes. A tiny pure helper
(`isAvailable(id)`) gates every interaction and is unit-tested so a coming-soon
tool can never be selected, sent, or defaulted into.

**Honesty rule:** the registry gates the *UI*. The backend tool registry
(tools/01) is the real gate — a coming-soon tool simply isn't registered there,
so even a hand-crafted request can't run it. The frontend flag is presentation,
not security.

## Composer anatomy (mock, top to bottom)

Container: `--agent-bg-card`, 1px border (focus-within → brighter border),
radius card, sitting on a border-top strip of the panel.

1. **Textarea** — 2 rows base, auto-grows to a max (~8 rows), transparent,
   13.5px/1.5. Placeholder from the selected tool: `Ask the agent, or run code
   walkthrough…`. Draft is local state; cleared only after the send succeeds.
2. **Actions row** (6px gap):
   - **`NodeChip`** — the attached node (`main file`): square swatch + label +
     faint kind. Real source: current canvas selection (v1's composer already
     subscribes to it — same wiring, new skin). Improvement over the mock,
     which shows a static chip: the chip is dismissible (×) and absent when
     nothing is attached. Multiple selection → multiple chips, wrapping.
   - **`ToolPicker` trigger** — the accent-tinted button: play glyph + selected
     tool's `short` + ▾. Border brightens to full accent while the menu is open
     (mock's `pickerBorder`).
   - Spacer, then **`EffortPicker`** — trigger keeps the mock's quiet `◇ {level}`
     mono look (11px faint); opens the **`REASONING EFFORT`** menu on the shared
     **`PickerMenu`** shell (see below). Not a cycle — four levels with hints.
     Selection persists in `useAgentRunStore` and rides every send.
   - **Send button** — 32px, radius 9, accent-btn, up-arrow glyph. While a run
     is streaming it becomes **Stop** (square glyph, ghost-danger) — the single
     cancel affordance (03 deliberately has none).

**Keyboard.** Enter sends; Shift+Enter newlines; Escape closes the picker menu
first, else blurs. Disabled send (empty draft, no conversation backend) is
visually muted, still focusable, with a tooltip reason.

## ToolPicker menu

Built on **`PickerMenu.tsx`** (shared with `EffortPicker`). Radix Popover
anchored above the trigger (mock: 280px, popover bg, strong border, radius
card, shadow, 5px padding).

- Section label `TOOLS` (10px/700/.08em faint).
- One row per registry entry: icon tile (26px, accent-tinted) + name (13px/600)
  over desc (11px muted) + right-aligned ✓ (accent) on the selected row. Hover:
  raised bg.
- **Coming-soon rows**: rendered in full, but at ~55% opacity, icon tile
  desaturated to muted grays, `aria-disabled`, no hover raise, and a right-
  aligned `Soon` pill (mono 10px, raised bg, faint text) where the ✓ would sit.
  Clicking does nothing except a tooltip: "Coming soon — walkthrough is
  available today." They are *visible on purpose* — the menu is the product's
  roadmap billboard.
- Selection persists across sends (mock behavior, keep) but only among
  available tools — today that means walkthrough is always the selection.

## EffortPicker menu

Not in the mock (it shows static text — Yared's call 2026-07-14: make it a
dropdown like the tools menu). **`EffortPicker.tsx`** replaces any earlier
`EffortIndicator` sketch; both menus are built on **`PickerMenu.tsx`** — one
shared Radix Popover shell (`composer/PickerMenu.tsx`) so section chrome,
padding, border, and shadow are not duplicated between tool and effort pickers.

- Anchored above its trigger, narrower (~220px) than the tool menu (~280px).
- Section label **`REASONING EFFORT`** (10px/700/.08em faint).
- One row per level — the effort enum from harness/04, no frontend invention:

| Level | Row hint |
|---|---|
| off | no visible thinking |
| low | brief thinking |
| medium *(default)* | balanced — the settings default |
| high | thorough thinking, slower |

- Rows: level name (13px/600, capitalized) over the hint (11px muted), **✓** on
  the selected row — same anatomy as tool rows, but the icon tile holds a **`◇`
  glyph** (not a tool icon) so the two menus visually rhyme.
- **Trigger** keeps the mock's quiet mono look (`◇ medium`, 11px faint); text
  updates with the selection (`◇ high`, etc.). Trigger tint brightens while
  open, matching the tool picker's `pickerBorder` treatment.
- **State:** selected level lives in `useAgentRunStore.effort`, persists for the
  session/conversation, and rides **every send** via `options.effort` on the
  wire (frontend/05). Default `medium`. Escape closes the menu (composer handles
  menu-before-blur ordering).

## What "picking a tool" means (improved semantics)

In the mock, send = canned user text + canned ack + a tool card, i.e. the picker
*commands* a tool. That contradicts the v2 architecture (the **agent** routes;
README "design stance"). Real semantics:

- The picker sets a **tool hint** on the outgoing message (a typed field on the
  send request, alongside text, node refs, and effort).
- Empty draft + send = the tool's default prompt from the registry
  (`Generate a walkthrough of this node.`) as the actual user text — visible in
  the thread, honest in history (mock does this too; keep it).
- The backend treats the hint as strong intent for the orchestrator prompt —
  the agent still speaks first (its status line), still calls the tool through
  the normal estimate → confirm path. If the user's text plainly asks a
  question instead, the agent may answer directly; the hint biases, never
  forces.

This means the composer→wire contract is exactly one call: send(text, nodeRefs,
toolHint?, effort) — already the v1 request shape plus `toolHint`; coordinate
the field addition with the backend (api/01) before V3.

## Build steps for this doc

1. `tools/registry.ts` + gating helper + tests.
2. Composer layout: textarea + send wired to the moved send path (V1 already
   proved the path; this is reskin + autosize + keyboard).
3. `NodeChip` from canvas selection, dismissible.
4. `ToolPicker` with coming-soon rendering; selection state in the composer.
5. `toolHint` field through the send request (backend coordination point).
6. `PickerMenu` shared shell → `EffortPicker` dropdown (`REASONING EFFORT`, ◇
   tile, four hinted rows, ✓ on selection); Stop-while-streaming swap on the
   send button.
