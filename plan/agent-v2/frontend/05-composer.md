# Frontend 05 — The Composer

The bottom of the panel: text input, node attachment chips, quick actions, and
the send/stop control. `AgentChatInput` grows into this; nothing else in the
chrome moves.

```
┌──────────────────────────────────────────────────┐
│ ┌──────────────────┐                             │
│ │ ⬡ charge (fn)  ✕ │        ← attachment chips   │
│ └──────────────────┘                             │
│ ┌──────────────────────────────────────────────┐ │
│ │ walk me through how retries hit this…        │ │  ← auto-growing textarea
│ └──────────────────────────────────────────────┘ │
│  [⬡ Attach selected]  [▶ Walkthrough]  [✧ Med ▾]  [➤]  │  ← quick actions · effort · send
└──────────────────────────────────────────────────┘
```

## Effort — how hard should it think

A small dropdown (`✧ off / low / medium / high`, default from the backend's
`AGENT_REASONING_EFFORT`) that sets the reasoning effort for the *next* runs; it
travels as `options: {effort}` on the message POST and sticks for the
conversation until changed (harness/04).

- **Why in the composer and not in settings**: effort is a per-question decision
  ("quick answer" vs "think hard about this refactor") — the same reason Cursor
  and Codex put it next to the model picker, one click from typing.
- Hidden entirely when the active model's capability is `channel: "none"` — a
  knob that does nothing must not render.
- The applied effort shows up later in the message metadata footer (03) with the
  reasoning-token count — the knob has a visible price, which is what keeps it
  meaningful.

## Node attachment — selection first, drag-drop later

**Decision: the chip source is the canvas selection.** A "⬡ Attach selected"
button reads `useProjectStore.selectedNode[activeTabId]` — exactly where the old
Launcher got its node — and adds a chip. Chips carry the full `NodeRefPart`
payload (`node_id`, `name`, `qname`, `node_type`) so the backend never looks
anything up to understand the message.

**Why selection before drag-drop.** It reuses a store read that already works,
needs zero canvas changes, and matches how users actually work (the node they
care about is the one they just clicked). Drag-from-canvas-to-composer is a pure
enhancement later — it produces the same chip, so nothing downstream changes.

Chip rules:

- max 3 chips (the backend's full-enrichment cap — context/03); the button
  disables at 3 with a tooltip saying why;
- chips persist until sent or removed (✕) — they do **not** follow the canvas
  selection after attaching (the user pinned a meaning; don't mutate it);
- clicking a chip focuses that node on the canvas (same affordance as chips in
  the thread, 03).

## Quick actions are canned messages — not code paths

`[▶ Walkthrough]` inserts the message *"Generate a walkthrough of this node."*
(with the attached chip) and sends it. That's all it does.

**Why.** One flow to test. The button is onboarding sugar; the agent does the
same intent-distillation it would do for typed text. This is how the old
Launcher's UX survives without keeping a second, parallel "launch" path alive —
the exact trap the MVP's launcher was designed to escape from later.

## Send / Stop

| Run status (from mirror) | Control |
|---|---|
| `idle` | ➤ send — enabled when text or chips are non-empty |
| `running` | ⏹ stop — calls `useRunStream.stop()` (POST /cancel + abort). The textarea stays *editable* — users draft the next message while a tour generates — but send is queued-disabled with "waiting for the current run" |
| `awaiting_confirmation` | composer disabled, hint: "waiting for your decision above" (the decision belongs on the card, not down here — one place to act) |

Keyboard: Enter sends, Shift+Enter newlines (the convention every chat user
already has in their fingers); Esc while running focuses the Stop button but
never auto-cancels — destructive actions are never one accidental keypress.

## Empty states (the first 10 seconds of the feature)

- No conversation yet: a centered hint in the thread — "Attach a node and ask
  about it, or ask for a walkthrough." plus the quick-action row. No fake sample
  messages (they train users that content is decorative).
- Node selected but nothing attached: the Attach button gently pulses **once**
  when the panel opens with a selection present — discovery without nagging.

## What the composer never does

| Never | Why |
|---|---|
| resolve names → node ids client-side | ids come from selection payloads only; the client must not become a second source of (possibly stale) graph truth |
| edit/rewrite the text before sending | the backend receives exactly what the user typed (context/03's audit rule, client side) |
| carry a depth/verbosity picker | those live on the confirmation card (06), where they have an estimate and a real max next to them — a knob without its cost context is how the MVP's launcher UX got awkward |
