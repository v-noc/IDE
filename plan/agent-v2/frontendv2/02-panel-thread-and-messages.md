# Frontend v2 — 02: Panel, Thread, Messages

The chrome and the conversation surface — everything visible before a tool card
appears. All data comes from the moved stores; nothing here talks to the network
directly.

## Panel chrome

**Layout (from the mock).** The panel is a fixed `420px` column on the right,
`--agent-bg-panel`, 1px left border. The canvas keeps flexing beside it — the
mock's `showCanvas` toggle corresponds to the existing open/close behavior.

**Mount seam.** v1 mounts via `features/Agent/index.tsx` → `AgentOverlay`,
consumed by `Main/components/WorkspaceLayout.tsx`. V2 keeps that exact seam:
`AgentV2/index.tsx` exports the same-shaped component, and during the transition
a dev switch picks which feature `WorkspaceLayout` imports (06). The overlay
open/close state stays in the existing `useAgentOverlayStore` — moved, not
rewritten.

**`AgentPanel.tsx`** is a dumb three-slot layout:

```
<PanelHeader />        48px, border-bottom
<ChatThread />         flex-1, overflow-y auto
<Composer />           border-top, own padding
```

**`PanelHeader.tsx`** — left to right (mock, verbatim):
- 7px status dot, `--agent-accent`. Improvement over the mock (which hardcodes
  green): the dot reflects run state — accent while a run streams (pulse),
  muted when idle, warn while awaiting confirmation. One `cva` variant, driven
  by a `useAgentRunStore` selector.
- `AGENT` — 13px / 650 / letter-spacing .04em.
- Right-aligned: `session 372f9c6e` — mono 10.5px, faint. Real value: first 8
  chars of the active conversation id; hidden when no conversation exists yet.

## ChatThread

**Data.** One selector produces the render list: ordered messages, each user
message with its attached-node refs, each assistant message as its ordered part
list. The thread maps over it and dispatches:

| Item | Component |
|---|---|
| user message | `UserMessage` |
| assistant text part | `AgentMessage` (wraps `TextPart`) |
| assistant reasoning part | `ReasoningPart` (spec unchanged from frontend/04) |
| assistant tool part | `ToolCard` (doc 03) |
| artifact render hint | `artifacts/registry` (frontend/07 bridge) |

Keys are part ids from the wire — never array indices (parts stream in and
mutate; index keys would remount mid-stream).

**Auto-scroll.** Same law as frontend/03, restated because the rebuild must not
lose it: stick to bottom while the user is at the bottom; any upward scroll
breaks the stick; new content while unstuck shows nothing louder than the scroll
position (no jump). Streaming text growth counts as new content. Implement once
in `ChatThread` (a ref + a `isPinned` flag on scroll events); no child manages
scrolling.

**Virtualization seam.** Not virtualized in V1 — conversations are short. Keep
the message list rendering behind one `renderItem(item)` function so dropping in
`@tanstack/react-virtual` later (already a dependency) touches one file.

## UserMessage

The mock, precisely:
- Card: `--agent-bg-card`, 1px `--agent-border`, radius card, padding 12/14.
- Header row: `YOU` (10.5px / 700 / .08em, faint) followed by the node chips.
- Chips (`NodeRefChip`): pill, mono 11px, `--agent-bg-raised` +
  `--agent-border-strong`, a 6px square swatch, then `label` + a fainter `kind`
  (`main file`). One chip per attached node ref on the message.
- Body: 13.5px / 1.55, `--agent-text` at ~90% (`#dfe2e7` in the mock). Plain
  text, pre-wrap — user input is never rendered as markdown.

## AgentMessage

Deliberately quieter than the user card — no box at all (mock: bare padding):
- `AGENT` label — 10.5px / 700 / .08em in the desaturated accent (`#4ea877` →
  token, not raw).
- Body: streaming markdown via the existing `TextPart` approach —
  `react-markdown` + `remark-gfm`, streamed text appended by the mirror store;
  markdown re-parses per frame, which is fine at chat sizes (measured in v1).
- Links inside markdown use `--agent-accent-link`.

The mock shows agent acks as single sentences ("I'll generate a step-by-step
walkthrough…") — that's exactly the harness/04 status line arriving as a normal
text part before the tool part. No special casing: it renders like any agent
text.

## ReasoningPart (delta from mock)

The mock has no thinking row; the product does (frontend/04 — live clamped tail
→ "Thought for 3s" collapse). Restyle only: the collapsed row uses faint text +
mono duration, the expanded body uses `--agent-bg-inset` like other inset
surfaces. Behavior spec unchanged — do not re-derive it here.

## Build steps for this doc

1. `theme/tokens.css` + panel skeleton (`AgentPanel`, `PanelHeader`) rendering
   against a hardcoded empty conversation — verify tokens/fonts.
2. Move `stream/`, `store/`, `hooks/` from v1; run their tests untouched.
3. `ChatThread` + `UserMessage` + `AgentMessage`/`TextPart` + `NodeRefChip`
   against a real streamed conversation (fake-LLM provider works for this).
4. Auto-scroll rules; verify with a long streaming answer.
5. `ReasoningPart` restyle on a reasoning-capable model.
