# 08 — Expand everything on Play; focus once, then slide

## The problems

1. **Per-step expansion feels broken.** The executor expands nodes one step at a
   time; combined with the lazy-children bug (fix 06) and injection latency, nodes
   pop in mid-tour and the layout reshuffles under the user.
2. **The camera "focuses" every node.** Every step re-centers at zoom 1 — a hard cut
   per step. The user wants: one real focus on the **tour's root** when Play starts,
   then gentle **slides** between stops, keeping the user's zoom.
3. **Hidden double-driver:** the camera is currently driven from TWO places —
   `useStepExecutor.panToNode` AND `CanvasView`'s own `centerOnTarget` effect, which
   fires on every selection change (the executor selects every step) and re-centers
   at `zoom: 1`. On top of that, the executor uses `handleNodeSelection(..,
   "primary")`, which for **call nodes** creates/destroys "Explore" portal tabs as a
   side effect — chaos during a tour that visits calls.

Fix 06 must land before this one.

## Target behavior (write this into the code as a comment on `play()`)

> On Play: materialize and expand every tour stop up front, so the canvas layout is
> final before the first step. Then: step 0 → one centered focus (zoom 1) on the
> tour root; every later step → smooth pan at the **current** zoom, only if the node
> is not already fully visible. The walkthrough drives the camera alone while
> playing; selection-centering and portal-tab side effects are suppressed.

## Files

| File | Action |
|---|---|
| `walkthrough/executor/prepareTour.ts` | NEW — expand + prefetch all stops before playing |
| `walkthrough/store/useWalkthroughStore.ts` | `play()` calls prepare; new `preparing` flag |
| `walkthrough/executor/useStepExecutor.ts` | selection without side effects; slide-vs-focus camera; stop per-step expansion |
| `Canvas/components/CanvasView.tsx` | suppress `centerOnTarget` while a tour is playing |

## Step A — `prepareTour.ts`

```ts
export async function prepareTour(
  queryClient: QueryClient,
  tabId: string,
  session: WalkthroughSession,
): Promise<void>
```

1. Collect ids: every `visit_list.nodes[*].node_id`, **plus** each stop's ancestor
   path. Getting ancestors: run `ensureOnCanvas` for each stop **sequentially in
   visit order** (it already resolves lineage, pushes focus, expands the path —
   reuse it, do not reimplement). Sequential, not `Promise.all` — lineage fetches
   share ancestors and the react-query cache dedupes them; parallel would just spike
   the backend.
2. After the loop, call `expandNodesBulk(tabId, [...allStopIds])` once, so every
   stop that HAS children shows them (with fix 06, their lazy children will render
   as fetches land).
3. Do **not** open any code view here (`codeOpenNodeId` stays per-step — opening N
   Monaco editors at once is the wrong kind of "available").
4. Restore focus to the tour root when done: the loop leaves focus on the LAST
   stop's lineage; finish with `ensureOnCanvas(queryClient, tabId, visit_list.nodes[0].node_id)`.
5. Failures: per-stop try/catch; collect failed ids, `toast` once ("N stops could
   not be loaded"), continue. Never throw out of prepareTour.

## Step B — store wiring (no useEffect)

In `useWalkthroughStore.play()`:

- Set a new flag `preparing: true`, capture `savedView` (as today), THEN run
  `void prepareTour(...)` and on completion set `preparing: false; phase: "playing";
  cursor: cursor < 0 ? 0 : cursor`. Until then phase stays as it was — the Play
  button (fix 02's PlayControls) shows "Preparing…" while `preparing`.
- `prepareTour` needs `queryClient`: import the module-level `queryClient` from
  `src/frontend/src/lib/queryClient.ts` (same instance the app uses — verified
  pattern, `useTabStore` already imports it).
- This is an **event-driven async action** started by a user click — exactly where
  async belongs. No new `useEffect` anywhere in this fix.

## Step C — executor changes (`useStepExecutor.ts`)

1. **Selection without side effects.**
   > ⚠ **CORRECTED — see fix 09 before doing this step.** The original instruction
   > here said to use `setSelectedNode`. That removed the portal-tab side effect but
   > introduced a worse one: in this canvas, primary selection IS the layout root,
   > so selecting each stop re-roots the canvas and hides every other node. The
   > correct call is `setSecondarySelectedNode` (highlight without re-rooting), and
   > `ensureOnCanvas` must stop writing focus during playback. Full explanation and
   > steps in `09-spotlight-not-reroot.md`. The rest of this doc stands.
2. **No per-step expansion.** Delete the `expandNode` call from the `show_code`
   branch — prepareTour already expanded everything. Keep setting
   `codeOpenNodeId` (that is what opens the Monaco view via `useNodeCode`).
3. **Slide vs focus.** Replace `panToNode` with:

```ts
function moveCameraToStep(tabId: string, nodeId: string, isTourRoot: boolean) {
  const instance = getCanvasInstance(tabId);
  const rfNode = instance?.getNode(nodeId);
  if (!instance || !rfNode?.measured?.width) { /* capped rAF retry, fix 03-F5 */ }

  const cx = rfNode.position.x + rfNode.measured.width / 2;
  const cy = rfNode.position.y + rfNode.measured.height / 2;

  if (isTourRoot) {
    instance.setCenter(cx, cy, { zoom: 1, duration: 500 });   // the one real focus
    return;
  }
  // slide: keep the user's zoom; skip entirely if already fully in view
  const zoom = instance.getZoom();
  if (isNodeFullyInViewport(instance, rfNode)) return;
  instance.setCenter(cx, cy, { zoom, duration: 600 });
}
```

   - `isTourRoot` = `step.visitOrder === 0 && step.id.endsWith === intro` — simpler:
     `cursor === 0`. Use `cursor === 0`.
   - `isNodeFullyInViewport`: compute from `instance.getViewport()` (x, y, zoom) and
     the canvas element size vs the node rect — write it as a pure exported function
     next to `lineMapping.ts` with a unit test (viewport math: a node at flow
     coords maps to screen via `screen = flow * zoom + viewportOffset`). Include a
     margin (say 48 px) so "barely visible at the edge" still slides.
   - Block-to-block steps within the same node: the node is already in view →
     no camera motion at all. That is the calm the user is asking for.
4. `userInteracted` still suppresses the slide (unchanged behavior, already reset
   per step).

## Step D — single camera driver (`CanvasView.tsx`)

In the `centerOnTarget` effect-event (search `lastCenteredTargetIdRef`): bail out at
the top when a tour is playing:

```ts
if (useWalkthroughStore.getState().phase === "playing") return;
```

Reading store state inside the existing effect-event is enough — no new effect, no
new subscription; when the tour ends, normal selection-centering resumes untouched.
(Without this, every step gets double-centered at zoom 1 — this line is the single
biggest "why does it jump around" fix.)

## Prove it

1. Play on a class at depth 1: BEFORE step 1 appears, all stops are already on the
   canvas, expanded, laid out (watch: no layout reshuffle during the tour).
2. Step 0: one centered zoom-1 focus on the tour root, with the fix-07 ring.
3. Zoom out to 50 % → Next through the tour: camera **slides** between nodes at
   50 % zoom, never snapping to zoom 1; block→block steps inside one node cause no
   camera motion.
4. Tour over calls: no "Explore" tabs appear during playback (Step C-1).
5. Pan away mid-step → no re-centering until Next (userInteracted respected);
   selection clicks on other nodes don't recenter either (Step D suppression), and
   the tour recovers on the next step.
6. Exit → selection-centering behaves as before the tour (click a node in the
   sidebar: it centers — the suppression really was playing-only).
7. `yarn test` green, plus the new `isNodeFullyInViewport` unit test.
