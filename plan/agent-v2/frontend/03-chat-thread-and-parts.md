# Frontend 03 — Chat Thread and the Part Renderers

The thread is a dumb list; all intelligence lives in a **part registry**: every
part `type` maps to exactly one component. Unknown types render a fallback chip
instead of crashing — the backend can ship a new part type before the frontend
learns it.

## The registry

```tsx
// chat/parts/registry.ts
const PART_COMPONENTS: Record<string, React.FC<PartProps>> = {
  text:      TextPartView,
  reasoning: ReasoningPartView,    // 04 — native CoT, collapsible thinking row
  tool:      ToolPartView,         // 06 — card shell + confirm + progress
  node_ref:  NodeRefChipView,
  decision:  null,                 // decisions render INSIDE their tool card, not standalone
};
// unknown type → <UnknownPartChip type={part.type} />
```

**Why a registry and not a switch in the thread.** Same reason as the backend's
tool registry: adding a part type must not touch the thread, auto-scroll, or
message layout. One file changes.

## Message layout

```
┌────────────────────────────────────────────┐
│ ● you                                      │   user message:
│ ┌──────────┐                               │   node chips row (if any)
│ │ ⬡ charge │  walk me through how retries  │   + text
│ └──────────┘  end up calling this twice    │
│                                            │
│ ✦ agent                                    │   assistant message:
│ ▸ Thought for 12s                          │   reasoning row (04, if the model has one)
│ I'll tour charge at depth 1 — it's small.  │   status line: plain text before the tool
│ ┌ ⚙ walkthrough ────────────── running ┐   │   tool card (06)
│ │ ███████████░░░░░  charge (3/12)      │   │
│ └──────────────────────────────────────┘   │
│ Done — 12 stops, one fell back to its      │   text part (markdown)
│ stored description.                        │
│                        glm-4.7 · 2.1k tok  │   metadata footer (F4, subtle)
└────────────────────────────────────────────┘
```

- Parts render **in stored order** — the transcript is the truth, no reordering,
  no grouping magic. An assistant message is literally its parts, top to bottom.
- The metadata footer reads `message.metadata` (model, tokens) — one muted line,
  F4, hidden until then.
- `NodeRefChip` shows `⬡ name (kind)`; clicking it focuses the node on the canvas
  (the existing `setCenter` path the walkthrough executor already uses).

## Text parts — markdown, streamed

`TextPartView` renders `react-markdown` with the same component set as the
walkthrough's `StepMarkdown` (inline code, fenced blocks via the shiki
highlighter, no headings/images per the prompt rules) — **shared config, one
file**, so chat answers and tour popups read identically.

**Streaming performance decision.** Re-parsing markdown on every token is the
classic chat-UI trap. Three-layer defense, cheapest first:

1. frames are already rAF-coalesced (02) — at most ~60 store updates/s;
2. the part component subscribes to **its own path only** (zustand selector on
   `parts[i].text`), so a token append re-renders one component;
3. `react-markdown` output is memoized on `text` — during streaming that means
   re-parse per flush, which is fine for the short texts our prompts enforce
   ("2–4 sentences"); if profiling ever disagrees, the seam is
   `TextPartView`, and the fix is parse-on-settle (plain `whitespace-pre-wrap`
   text while `status === "streaming"`, markdown swap when the part settles).

**Why not virtualize the thread now.** `react-virtual` is in the repo, but
virtualization fights streaming auto-scroll and collapsibles for measurement.
Conversations are dozens of messages, not thousands. The seam is `ChatThread`
(map → virtual list); take it when a real conversation gets slow, not before.

## Auto-scroll (the detail everyone gets wrong)

- Pinned to bottom **only while the user is at the bottom** (threshold ~40 px).
  Any upward scroll unpins; a "↓ jump to latest" pill appears while streaming
  continues off-screen.
- New *user* message always scrolls to bottom (they just sent it).
- Expanding a collapsed thinking row or artifact never auto-scrolls — the user is
  reading; the UI must not yank.

## States the thread renders (from the conversation mirror, not local flags)

| Mirror state | Thread |
|---|---|
| assistant message exists, parts empty | typing indicator row (three-dot pulse) |
| `status: "running"` | streaming parts render live; composer shows Stop (05) |
| `status: "awaiting_confirmation"` | confirm card is the last visible thing; composer disabled with hint "waiting for your decision above" |
| `status: "error"` | inline error row under the last message: metadata.error text + "try again" (re-sends the last user message) |
| `stop_reason: "max_steps"` | the closing text part already explains (backend guarantees it); a muted "step limit reached" chip on the message footer |
| `stop_reason: "cancelled"` | muted "stopped" chip |

**Why everything derives from the mirror.** No local `isLoading` booleans to
drift out of sync — the same rule that made the walkthrough player reliable: the
document is the state machine, the UI is a projection of it.
