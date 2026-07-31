# Frontend 06 — Tool Card and the Confirmation UI

A `tool` part renders as **one card with five faces** — one per `ToolState`
status (data-model/01). The card never invents state: it is a pure projection of
the nested state object the backend streams.

## The shell

```tsx
// chat/tool/ToolCard.tsx
<ToolCard part={part}>            // header: icon · tool title · status chip
  {face for part.state.status}    // body swaps by status — the union makes
</ToolCard>                        // illegal combinations unrepresentable in TS too
```

Header: a friendly title per tool (`walkthrough` → "Code walkthrough"), a status
`Badge`, and a ⚠ badge when `degraded` — visible honesty, same as the tour
outline today.

## The five faces

### 1 · `pending` / `estimating`
One muted row: "Preparing… / Estimating cost…" with the shimmer. No skeleton
theater — it lasts under a second.

### 2 · `awaiting_confirmation` — the confirmation card

```
┌ ⚙ Code walkthrough ─────────────── needs approval ┐
│                                                    │
│  charge (function) · 12 stops · ~30 LLM calls      │  ← estimate.label
│                                                    │
│  Depth        0 ──●──────── 3   (this tree: max 3) │  ← slider, prefilled w/
│               │ 2 levels below charge │            │    agent's suggestion,
│                                                    │    max from knobs.depth.max
│  Detail       ( Quick | ● Normal | Detailed )      │  ← toggle-group
│                                                    │
│  ⚠ Bigger than the auto-run limit — that's why     │  ← only when over threshold
│    we're asking.                                   │
│                                                    │
│              [ Cancel ]        [ ▶ Run tour ]      │
└────────────────────────────────────────────────────┘
```

Decisions and whys:

- **The slider max is the backend's `knobs.depth.max`** (the WOQL subtree probe,
  harness/03) — the UI physically cannot ask for a depth that doesn't exist.
  Ticks beyond the subtree max simply aren't there; a caption says
  "this tree: max 3" so the missing range reads as fact, not as a broken control.
- **Changing depth re-estimates live** — debounced call to the estimate endpoint
  (the old Launcher already did exactly this; the pattern moves here). The label
  updates in place: "12 stops · ~30 calls" → "4 stops · ~9 calls". A knob without
  a live price is a guess.
- **Approve** → `useDecision.decide(toolCallId, "approve", {depth, verbosity})` —
  only *changed* values go into `overrides`. **Cancel** → `"cancel"`; the agent
  gets a "declined" result and answers gracefully — cancel is a first-class
  answer, not an error, so the button is quiet, not red.
- Buttons disable the instant a decision posts (double-click safety); the card
  face flips when the resumed stream confirms.
- `estimate.over_cap` renders a different card: no Run button at all, the
  refusal message, and a hint to lower depth — refusal is the backend's call; the
  UI just doesn't pretend otherwise.

### 3 · `running`

```
┌ ⚙ Code walkthrough ──────────────────── running ┐
│ ████████████░░░░░░░░  charge (3/12)      [Stop] │
│ ▸ tour is playable while it generates — Play ▶  │   ← walkthrough only (07)
└──────────────────────────────────────────────────┘
```

`Progress` bar from `state.progress.{done,total}`, the code-authored label
verbatim (it is the only trustworthy narration — zero tokens, zero
hallucination). Stop here cancels the whole run — same handler as the composer's
stop, one code path.

### 4 · `completed`

Collapsed summary row — "12 stops · 31 steps · 1 fallback ⚠" — plus the
**artifact body** mounted below it via the render-hint registry (07). The
compact `result` dict is model-facing; the UI shows the artifact, not the JSON.

### 5 · `error`

One amber row: the error text, no stack traces, no red-screen drama — the turn
continued (the agent already explained in its following text part), so the card
must not look like the conversation died. "declined by user" renders as a muted
"cancelled — you declined" face, distinct from real errors.

## The decision record

After a decision, the card keeps a one-line receipt: "approved · depth 2 ·
normal" or "declined". This is the `DecisionPart` made visible — the transcript
shows what the user chose, which matters when someone reads the conversation
later (or when the user disputes what they approved).

## Reload behavior

All faces render correctly from a seeded mirror (02): a conversation reloaded
mid-`awaiting_confirmation` shows the live confirm card (decide still works —
or a "run expired" face on 409); a reloaded `completed` card lazy-loads its
artifact on mount. No face depends on having watched the stream.
