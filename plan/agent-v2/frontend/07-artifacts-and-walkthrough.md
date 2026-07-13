# Frontend 07 — Artifacts and the Walkthrough Bridge

How rich tool output renders. A completed (or streaming) task tool carries an
`ArtifactRef {doc, render}`; the `render` hint picks a component from a registry,
and the component reads the artifact's **own mirror doc** — never the tool part.

## The artifact registry

```tsx
// chat/artifacts/registry.ts
const ARTIFACT_RENDERERS: Record<string, React.FC<{ doc: string }>> = {
  walkthrough: WalkthroughArtifact,
  // later: run_checklist (describe/document runs), node_cards (search)
};
// unknown render hint → <UnknownArtifactChip doc={…} /> with a raw "open" link
```

**Why hint-based and not tool-based.** Two future tools can share one renderer
(describe and document both want a checklist); the backend already made `render`
a first-class field for exactly this reason.

## The walkthrough bridge — mount the player, change nothing in it

The existing walkthrough feature is a working machine:
`useWalkthroughStore` (session + phase) → `flatten.ts` (PlayerSteps) →
`useStepExecutor` (canvas movement, Monaco lines, popovers). v2 does **not**
reach into any of it. Instead, one small bridge:

```ts
// walkthrough/bridge.ts
export function useWalkthroughBridge(doc: string) {
  // subscribe to useMirrorStore.docs[doc]
  // → feed session snapshots into useWalkthroughStore (the same setters the
  //   NDJSON source calls today: hello-equivalent on first snapshot, then updates)
  // → map mirror status open/closed/error onto phase generating/ready/error
}
```

```tsx
// chat/artifacts/WalkthroughArtifact.tsx
function WalkthroughArtifact({ doc }: { doc: string }) {
  useWalkthroughBridge(doc);                    // mirror → player store
  useArtifactLoader(doc);                       // reload path: GET artifact if mirror is empty
  return <TourOutline />;                       // the existing component, as-is
}
```

**Why a bridge instead of refactoring the player onto the mirror store.** The
player's store is also its playback state machine (phase, current step, armed
popovers) — live UI state that does not belong in document mirrors. Splitting
"document" (mirror) from "playback" (walkthrough store) along the existing line
costs one ~40-line hook and zero regression risk. If the walkthrough store ever
gets rebuilt, the bridge is the only file that knows both sides.

Playback-while-generating survives automatically: the mirror updates as patches
arrive, the bridge feeds the store, and the player's existing
"play while `generating`" behavior does the rest — the MVP already proved this
flow; v2 just changes who delivers the frames.

## In-thread vs expanded

- **In thread**: `TourOutline` renders inside the tool card body — compact,
  scrollable, playable (the outline's Play arms the canvas overlay exactly as
  today).
- **Expand**: a button on the card header switches the sidebar to the
  walkthrough view (the existing `viewMode` toggle becomes this — it stops being
  a global mode and becomes "this artifact, big"). Same store, same player;
  purely a layout swap.

**Why keep in-thread as the default.** The conversation is the spine — the user
asked in chat, the answer lives in chat, and scrolling back a week later finds
the tour where the question was. Expansion is for the actual guided reading.

## Artifact loading rules

| Situation | Behavior |
|---|---|
| streaming live | the mirror doc was `open`ed on the same stream; render immediately, steps fill in |
| reload, artifact visible | `useArtifactLoader` fetches the artifact snapshot once, seeds the mirror (`closed`), player mounts ready |
| reload, artifact off-screen | nothing fetched until the card scrolls into view (`IntersectionObserver`) — a 20-tour conversation must not fire 20 fetches on open |
| artifact doc missing (crashed run, partial persist) | the card's completed face shows the summary + "partial artifact — {status}" chip; whatever stops persisted still render (truthful partial record, end to end) |

## Degradation, visibly

`degraded` on the tool part → ⚠ on the card header; degraded stops inside the
session already render their fallback styling in `TourOutline`/`StepCard` today.
Nothing new to build — the honest-UI muscle from the MVP carries straight
through. The rule stays: **the UI never hides a fallback.**
