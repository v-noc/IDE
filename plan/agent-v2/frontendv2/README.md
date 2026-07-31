# Frontend v2 — Agent Panel Redesign (the mock made real)

The agent chat surface shipped (plan/agent-v2/frontend, phases F1–F4: stream layer,
mirror store, parts, tool cards, composer all exist under `features/Agent/`). It
works, but it was built protocol-first — the visuals grew organically around the
wire. This plan takes the **Claude-design mock** (`design/agent-panel.dc.html`,
open it in a browser — `support.js` beside it is just the mock's runtime) and
rebuilds the *presentation layer* in a clean folder, to the mock's design, with
React best practices throughout.

**The one-sentence scope:** the protocol/data layer moves unchanged; every pixel
is rebuilt; all four tools are visible everywhere but only `walkthrough` is
enabled — the rest are "coming soon".

## Decisions (settled here, argued below)

| # | Decision | Why |
|---|---|---|
| 1 | "frontendv2" = `src/frontend/src/features/Dashboard/features/Agent/`, **not** a second Vite app | The mock's left half *is* the existing canvas (xyflow, Monaco, node cards). A `src/frontendv2/` app would fork all of that for zero design gain. The new design is a panel + overlays — a feature folder is the honest size. |
| 2 | **Keep** the data layer, **rebuild** the presentation | `stream/` (types, source, applyFrame + tests), `store/` (mirror, run, conversation, selectors), `hooks/` (useRunStream, useDecision) encode the wire contract and have tests. A redesign is a skin; forking the protocol code would create two sources of truth. They stay in `Agent/`; only presentation files were replaced. |
| 3 | Every visible component is written fresh against the mock | The v1 `chat/` components carry fixture-era decisions (v1 ConfirmCard separate from ToolCard, launcher-era spacing). Rebuilding is cheaper than restyling — and it's the only way the folder ends up *clean*. |
| 4 | Walkthrough player/executor logic untouched; its **components** restyled | `walkthrough/executor/`, `store/`, `source/` solve hard problems (line mapping, viewport, playback state) — untouched. `walkthrough/components/` (StepCard, progress pill, outline) get the mock's skin in phase V3. |
| 5 | All four tools rendered, one enabled | A frontend **tool registry** is the single source: `walkthrough: available`; `describe`, `document`, `group`: `coming-soon` (they land with plan/agent-v3). Coming-soon tools appear in the picker disabled with a "Soon" badge; their card faces are specced in 03 but not built until their backends exist. |
| 6 | Mock hexes become semantic tokens | No `#3ecf72` in components. One tokens file maps the mock's palette to semantic CSS variables (Tailwind 4 `@theme`), so the panel can later follow the app theme. See 01. |
| 7 | Old `Agent/` presentation retired at the end, not the start | New panel mounts in place of v1 presentation files (06); legacy chat/tool UI deleted once parity is reached. |

## Design → system mapping (what the mock's fixtures really are)

The mock is a static fixture player — every dynamic value in it corresponds to
something the real system already provides. This table is the contract for the
rebuild; each doc references it.

| Mock element | Mock source | Real source |
|---|---|---|
| session id in header (`session 372f9c6e`) | hardcoded | short hash of the active conversation id (`useAgentRunStore`) |
| user message + node chips | fixture `messages` | user message parts + attached-node refs from the conversation store |
| agent ack text ("I'll generate a step-by-step…") | canned per tool | real streamed text part — the status sentence the agent emits before a tool call (harness/04) |
| tool card `status: pending` | fixture | tool part state `awaiting_confirmation` (backend interrupt, harness/03) |
| depth max ("this tree: max 4") | `TOOLS[k].treeMax` | real subtree max depth from the estimate payload (WOQL probe, hard cap 5) |
| "Run tour" button | starts a `setInterval` | POST to the decision endpoint (`useDecision`) with the edited config |
| progress `3 / 9 steps` | timer ticks | patch stream progress on the tool part |
| tour outline rows | `OUTLINE` fixture | walkthrough artifact doc (mirror store) — same data the player consumes |
| "Play walkthrough" | toggles fixture playback | mounts the existing player via the artifact bridge (frontend/07) |
| step card / bottom pill / node glow | fixture `TOUR_STEPS` | existing `useWalkthroughStore` + executor — restyle only (05) |
| tool picker menu | picks the fixture tool | tool registry (04); coming-soon rows disabled |
| `◇ medium` in composer | hardcoded static text | **`EffortPicker`** dropdown — same `PickerMenu` popover shell as the tool picker; trigger keeps the quiet `◇ {level}` look; `REASONING EFFORT` menu with four hinted rows (04) |

## What the mock gets wrong (improve, don't transcribe)

- **Inline styles everywhere** — mock artifact. The rebuild uses Tailwind
  utilities + `cva` variants over semantic tokens (01).
- **The picker "runs" a tool** — in the mock, send = canned user text + canned
  ack + tool card. Real flow: send a message, the *agent* decides. The picker is
  a **hint** (prefills the prompt, biases intent), never a bypass of the agent (04).
- **No error state** — the mock has pending/running/done/cancelled. Real tools
  fail; 03 adds the error face (failure is boring: card turns quiet-red, agent
  answers anyway).
- **Client-side config defaults** — the mock invents depth/detail defaults; real
  defaults come from the agent's suggestion inside the estimate payload.
- **Effort is dead text** — the mock renders `◇ medium` as inert label text. It
  becomes **`EffortPicker`**: a dropdown on the shared `PickerMenu` shell,
  rhyming with the tool menu (◇ glyph in the icon slot, `REASONING EFFORT`
  section, off/low/medium/high with hints, ✓ on the selected row). The trigger
  keeps the mock's quiet mono look and updates with the selection; the value
  persists in `useAgentRunStore` and rides every send (04).
- **No thinking row** — the mock only shows final text. The Cursor-style thinking
  UI (frontend/04) still applies; it slots above the first text part unchanged.

## Docs in this folder

| Doc | Contents |
|---|---|
| 01 | target folder tree · React conventions the folder must obey · design tokens table |
| 02 | panel chrome, header, chat thread, user/agent messages, auto-scroll |
| 03 | the tool card: shell, five states, per-tool faces, config forms |
| 04 | composer, tool picker, coming-soon registry, **EffortPicker** (+ shared `PickerMenu`) |
| 05 | canvas playback restyle: step card, bottom pill, node highlight |
| 06 | build order V0–V4, demo gates, v1 retirement checklist |

## Phases at a glance

| Phase | Contents | Demo gate |
|---|---|---|
| **V0 — Scaffold** | folder + tokens + panel mount | Agent panel renders in the app, themed |
| **V1 — Thread** | header, thread, user/agent messages, minimal composer | chat streams end-to-end in the new skin |
| **V2 — Tool card** | card shell + walkthrough face (confirm form, progress, done outline) wired to decision endpoint | full walkthrough flow in the new skin |
| **V3 — Picker & playback** | tool picker with coming-soon rows · **EffortPicker** (`PickerMenu` shell) · playback overlays restyled | pick walkthrough, run a tour, overlays match the mock |
| **V4 — Retire v1** | error/cancelled states, thinking row, a11y & reduced-motion pass, delete v1 presentation | one `Agent/` feature folder remains |
