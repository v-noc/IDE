# Frontend v2 — 05: Canvas Playback Restyle

The mock's left half during a tour: a floating **step card**, a bottom **pill**,
and a **glow** on the active node. All three exist in v1 (`walkthrough/
components/` + executor) — this doc is a *restyle with the executor untouched*.
No playback logic, line mapping, viewport math, or store shape changes here.

## What maps to what

| Mock element | Existing component | Work |
|---|---|---|
| step card (left overlay) | `StepCard.tsx` / `WalkthroughStepOverlay.tsx` | reskin to the mock |
| bottom floating pill | `WalkthroughProgressPill.tsx` | reskin |
| node border glow | canvas node styling via executor/canvas registry | new highlight treatment |
| Prev / Next / Exit | `PlayControls.tsx` + `useWalkthroughStore` | reskin, same actions |
| step text + chips | step data from the walkthrough store | render only |

The `walkthrough/` folder moves into `AgentV2/` in this phase (01 tree); moving
and restyling land together so imports change once.

## Step card (mock, precisely)

400px, radius 14, `--agent-bg-tool`, border `#2b2e35`→token, deep double shadow.

- **Header row**: 8px accent dot with soft glow · step title 16px/650 · right
  counter chip `2 / 9` (mono 11.5px, raised bg, bordered, radius 6).
- **Body**: 14px/1.65 body-text color. Rendered through the existing
  `StepMarkdown` (narration is markdown; the mock's plain strings are fixture
  simplification — don't regress to plain text).
- **Chip row**: node chips (mono 11.5px, accent-tinted bg/border, radius 5) —
  the step's referenced nodes; clicking one focuses that node on canvas
  (existing executor capability, keep wired).
- **Progress segments**: one 3px flex segment per step, done = accent, rest =
  raised. (The mock builds this from `stepDots`; real source is step
  index/count from the store.)
- **Footer**: `Exit tour` ghost left; right group `Prev` (ghost-bordered) and
  `Next` (primary accent-btn). Same actions the store exposes today; keyboard
  navigation from `useWalkthroughKeyboard` is unchanged.

Positioning stays executor-driven (the card places itself relative to the
focused node/viewport — v1 already solves this in `popoverLayout.ts` /
`WalkthroughStepOverlay`). The mock's fixed left placement is a fixture
simplification; do not adopt it.

## Bottom pill

Centered, bottom 20px, radius pill, `rgba(24,26,30,.92)` + backdrop blur,
bordered, floating shadow:

pulsing accent dot (static under reduced-motion) · step title 13px/600 ·
mono counter `2 / 9` · small `Exit` pill (bordered, raised).

The pill is the minimized/global affordance while the user pans away from the
step card — exactly what `WalkthroughProgressPill` does today. Keep its
show/hide logic; swap the skin.

## Active-node highlight

Mock treatment on the focused node: border `rgba(62,207,114,.6)` + ring shadow
`0 0 0 3px rgba(62,207,114,.15)` + soft drop shadow, transitioned (.3s). Apply
via a `data-walkthrough-active` attribute/class the executor already knows how
to target when focusing nodes (`ensureOnCanvas`/`canvasRegistry`) — the canvas
node component (`EnhancedNode`) gains one conditional class, nothing more.
Reduced-motion: no transition, ring still shown (the ring is information, the
animation is decoration).

## Playback entry/exit (wiring recap, unchanged)

- Enter: `Play walkthrough` on the done tool card (03) — artifact bridge mounts
  the player exactly as v1's `WalkthroughArtifact` does.
- Exit: any of `Exit tour` (card), `Exit` (pill), or the card button flipping to
  `Exit playback`. All call the same store action; playback state stays in
  `useWalkthroughStore` — the panel reads it only for that button label.
- While playback is active the panel stays fully interactive (mock shows both
  live) — no modal lock.

## Build steps for this doc

1. Move `walkthrough/` into `AgentV2/`; fix imports; run its tests
   (flatten/selectors/lineMapping/viewport) untouched.
2. Reskin `StepCard` + overlay (header/body/chips/segments/footer).
3. Reskin the pill.
4. Node highlight class in `EnhancedNode` + executor hookup.
5. Reduced-motion pass over dot/glow/transitions.
6. Full tour on a real project: card placement, chip-click focus, keyboard,
   exit paths.
