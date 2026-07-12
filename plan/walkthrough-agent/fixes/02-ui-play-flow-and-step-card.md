# 02 — Play flow and step card sizing

## The problems (what the user sees)

1. **Starting a tour is confusing.** After Generate, the step card overlay already
   appears (phase `generating`/`ready`) showing "Press Play to start the tour", but
   the Play button only renders inside the card under one specific condition
   (`phase === "ready" && cursor < 0` — see `StepCard.tsx`). While still generating
   there is no Play at all; clicking Next in that state silently jumps to step 0.
   There is no obvious "▶ Play" anywhere in the panel where the user is looking.
2. **The card width is wrong.** `StepCard` uses `w-full max-w-2xl` inside a
   full-width overlay row (`WalkthroughStepOverlay.tsx`), so it stretches to 672 px on
   wide screens, covering canvas nodes, and it sits at `bottom-4` where it can collide
   with the Sandbox bottom bar in `WorkspaceLayout.tsx`.
3. **Resume is broken.** `next()` in `useWalkthroughStore.ts` has an "implicit play"
   branch: when phase is not playing/generating it sets `cursor = 0` — so exiting at
   step 7 and pressing Next restarts at step 1 instead of resuming.

## Target behavior

- The **panel** owns starting: a primary "▶ Play walkthrough" button appears under
  the Launcher as soon as the first steps exist (even while still generating). Label
  becomes "Resume" when `cursor > 0`. Clicking an outline row also starts (already
  works via `jumpTo`).
- The **overlay card** appears only while `phase === "playing"`. No dead "Press
  Play" state inside it.
- The card has a fixed comfortable width and never covers the bottom bar.
- Exit keeps the position; Play/Next resume where the user left off.

## Files

| File | Action |
|---|---|
| `walkthrough/components/Launcher.tsx` or a new `PlayControls.tsx` | ADD the Play/Resume button |
| `walkthrough/components/StepCard.tsx` | Remove Play-inside-card + non-playing states; width |
| `walkthrough/components/WalkthroughStepOverlay.tsx` | Render only when playing; positioning |
| `walkthrough/store/useWalkthroughStore.ts` | Fix `next()` resume; queue-edge auto-advance |
| `walkthrough/index.tsx` | Mount `PlayControls`, update the "Generation complete" hint |

## Step A — store fixes first (UI reads these)

Open `walkthrough/store/useWalkthroughStore.ts` and make these exact changes:

1. **`next()`**: delete the implicit-play branch. New behavior:
   - if `phase !== "playing"` → do nothing (the UI must call `play()` instead);
   - else advance as today; if already at the last available step **and**
     `phase-of-generation` is still running (`session.status === "generating"`), set
     a new state flag `pendingAdvance = true` instead of doing nothing.
2. **`play()`**: keep current behavior (captures `savedView` once, keeps existing
   `cursor` when `>= 0` — verify this line exists:
   `state.cursor = state.cursor < 0 ? 0 : state.cursor;`).
3. **Auto-advance at the queue edge**: in `handleFrameResult`, after `syncDerived`,
   add: if `pendingAdvance && state.phase === "playing" && state.cursor <
   state.playerSteps.length - 1` → `state.cursor += 1; state.pendingAdvance = false`.
   Also clear `pendingAdvance` on `exit`, `discard`, `prev`, `jumpTo`.
4. Add `pendingAdvance: boolean` to state + `initialState`.

Careful: `handleFrameResult` currently **overwrites `phase` from the frame result**,
which has a separate bug when generation ends during playback — that is fixed in
`03-frontend-correctness.md` (F2). Do not fix it here; just be aware the two touch
the same function.

## Step B — PlayControls in the panel

New small component (or a section inside `Launcher.tsx` — prefer a new
`PlayControls.tsx` so Launcher stays "before generation" and PlayControls is "after"):

- Reads `phase`, `playerSteps.length`, `cursor` from the store.
- Renders nothing when `playerSteps.length === 0`.
- Renders a full-width primary button:
  - `phase === "playing"` → "⏸ Exit playback" (calls `exit()`), secondary style;
  - else → `cursor > 0 ? "▶ Resume (step N)" : "▶ Play walkthrough"` (calls `play()`).
- Under it, one muted line: `"{playerSteps.length} steps ready"` and, while
  `session.status === "generating"`, append "· still generating…".
- Mount it in `walkthrough/index.tsx` between `Launcher` and `TourOutline`. Remove
  the current `phase === "ready"` hint paragraph (PlayControls replaces it).

## Step C — StepCard: playing-only, fixed width

1. In `WalkthroughStepOverlay.tsx`: change the show condition to
   `phase === "playing"` only. Keep `useStepExecutor()` **above** the early return
   (hooks must run unconditionally — it already is; verify).
2. Positioning: the overlay row is `absolute inset-x-0 bottom-4`. Change to
   `bottom-20` (clears the Sandbox bottom bar — open `WorkspaceLayout.tsx`, find the
   bottom bar height, and pick the Tailwind bottom-* that clears it; verify visually)
   and keep `z-20`. Confirm nothing else in WorkspaceLayout uses a higher z-index
   that should sit above the card except dialogs.
3. In `StepCard.tsx`:
   - Replace `w-full max-w-2xl` with `w-[440px] max-w-[calc(100vw-2rem)]`.
   - Delete the `phase === "ready" && cursor < 0` Play branch and the
     "Press Play to start the tour." fallback text — with Step B, the card only ever
     renders during playback with a real step.
   - `canNext` becomes: `cursor < total - 1 || session?.status === "generating"`
     (read status via the store selector; when at the edge during generation the
     button stays enabled and `next()` sets `pendingAdvance`, showing the shimmer).
   - Keep Exit / Prev / Next and the ⚠ tooltip as they are.

## Step D — keyboard

`useWalkthroughKeyboard.ts` already guards inputs and only runs while playing —
verify nothing here needs the removed states. Escape → `exit()` still applies.

## Prove it

1. Generate on a real node (mock mode from fix 01). While the outline is still
   filling, "▶ Play walkthrough" is already visible and works.
2. The card appears only after pressing Play; it is ~440 px wide, centered, and does
   not cover the Sandbox bar.
3. Play → Next to step 3 → Esc → canvas restored → press Resume → you are back at
   step 3 (not step 1).
4. Hold Next until you outrun generation → shimmer shows → the card advances by
   itself when the next step's text arrives.
5. `yarn test` still green.
