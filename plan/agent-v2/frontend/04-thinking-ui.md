# Frontend 04 — The Thinking UI (Cursor-style collapse)

How `reasoning` parts render. *(Revised with harness/04: the thinking row shows
the model's **native** chain of thought — extracted deltas or the provider's
summary — never prompt-forced narration. If the model has no reasoning channel,
there is no row.)*

The user sees two distinct things, and they must not blur:

- **the thinking row** — the collapsible trace this doc covers (`reasoning` part,
  `origin: "native" | "summary"`);
- **the status line** — one short plain sentence before each tool call ("I'll
  tour `charge` at depth 1 — it's small"). That is an ordinary `text` part,
  rendered as normal message text (03) — always visible, never collapsed. It is
  the "small summary before the tool call"; the thinking row is the *evidence*,
  the status line is the *communication*.

## The two states of the row

### While streaming — visible, alive, but small

```
✦ agent
┌─────────────────────────────────────────────────┐
│ ✧ Thinking…                                     │  ← shimmer label
│   the user attached charge and wants the retry  │  ← native CoT streaming in,
│   path… traversal at depth 1 covers it, cost    │    clamped to last 3 lines
│   is small so confirmation may auto-run…        │    (older lines slide away)
└─────────────────────────────────────────────────┘
```

- Deltas stream in via `append` ops; the row appears on the first delta.
- **Clamp to the last ~3 lines** (anchored bottom): progress without the thread
  pumping taller. Click mid-stream opens the full trace.
- `origin: "summary"` streams the same way but the label reads **"Reasoning
  summary"** — honesty about the artifact: raw CoT is hidden by that provider
  (OpenAI-style), and pretending otherwise misleads.
- Reuse `GeneratingShimmer` for the label sweep.

### Settled — collapsed to one line

```
✦ agent
▸ Thought for 12s                                    ← muted, one line
I'll tour charge at depth 1 — it's small.            ← status line (plain text)
┌ ⚙ walkthrough … ┐
```

- On channel close the row auto-collapses to `▸ Thought for {n}s` (duration from
  `part.duration_ms`, set by the backend when the channel settles). No first-
  sentence preview: raw CoT openings are model-speak, not reader prose — unlike
  the old forced analysis, this text was never written for the user, so the
  header stays neutral (Cursor and Claude Code both do exactly this).
- Click toggles the full trace (Radix `Collapsible`). Expanded text renders as
  muted plain prose — visibly quieter than answers; reasoning may reference ids
  and internals, and the styling must whisper "trace, not answer".

## Rules (each with its why)

| Rule | Why |
|---|---|
| No reasoning part → no row, ever | fake thinking rows teach users to ignore real ones; backend guarantees the part only exists when a native channel produced it |
| Auto-collapse on settle; collapsed on reload | the trace served its purpose live; afterwards it's reference. Matches the backend never replaying reasoning into history |
| `summary` origin is labeled as a summary | the user should know whether they're reading the model's actual tokens or the provider's digest |
| Toggle never auto-scrolls (03's rule) | the user is reading; don't yank |
| One row per reasoning burst; several per message allowed | interleaved thinking (think → tool → think) renders as an honest ordered trace |
| Trace styling is muted/indented, distinct from answer text | nobody should quote thinking as the answer; hierarchy does the disclaiming silently |
| Effort is set in the composer (05), not on this row | the row shows what happened; changing what happens next belongs where the next message is written |

## Component sketch

```tsx
// chat/parts/ReasoningPart.tsx
function ReasoningPartView({ part, isStreaming }: PartProps<ReasoningPart>) {
  const [open, setOpen] = useState(false);
  const label = part.origin === "summary" ? "Reasoning summary" : "Thinking";
  if (isStreaming) return <LiveThinkingRow label={label} text={part.text} />;
  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger>▸ Thought for {fmtSecs(part.duration_ms)}</CollapsibleTrigger>
      <CollapsibleContent className="text-muted-foreground">{part.text}</CollapsibleContent>
    </Collapsible>
  );
}
```

`isStreaming` derives from the mirror (this part is last in the last message of a
`running` conversation and hasn't settled) — no local timers, no flags to desync.
