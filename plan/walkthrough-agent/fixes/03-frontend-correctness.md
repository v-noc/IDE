# 03 — Frontend correctness fixes

Bugs found in review. Each one: where, what is wrong, exact fix, proof. All paths are
under `src/frontend/src/features/Dashboard/features/Agent/walkthrough/` unless noted.

---

## F1 — zod schema rejects `project` stops (kills the whole tour)

**Where:** `types.ts`, `nodeTypeSchema = z.enum(["folder","file","class","function","call"])`.

**Wrong:** the backend `NodeType` (see `src/backend/app/walkthrough/schemas.py`)
includes `"project"`. If the user starts a tour from a project node, the hello
frame's visit list contains `node_type: "project"`, `parseFrame` fails, the frame is
dropped, and every following patch hits "patch before hello" → phase `error`. One
enum value kills the entire feature for that start node.

**Fix:** add `"project"` to `nodeTypeSchema`. Then search the frontend for places
that switch on `node_type` for walkthrough stops (flatten, OutlineRow icons) and make
sure `"project"` falls into the container/no-code path.

**Prove:** add a vitest case: `visitNodeSchema.parse({...node_type: "project"...})`
succeeds. Manual: start a tour from the project root node.

---

## F2 — end-of-generation kicks the user out of playback

**Where:** `source/applyFrame.ts`, `case "end"` returns `phase: "ready"`
unconditionally; `store/useWalkthroughStore.ts` `handleFrameResult` copies that phase
into the store.

**Wrong:** if the user is `playing` while generation finishes (the normal
play-while-generating flow), the end frame flips phase to `ready` — the step card
disappears mid-step (after fix 02 the card is playing-only, making this very
visible).

**Fix:** in `applyFrame`'s `end/complete` branch, return
`phase: current.phase === "playing" ? "playing" : "ready"`. Leave the error branch
as is (an error should stop playback — but note in the card/panel that generation
failed; the store already surfaces `error`).

**Prove:** vitest: `applyFrame({kind:"end",status:"complete"}, {phase:"playing",...})`
returns `phase: "playing"`. Manual: press Play immediately after Generate and stay on
a step until the outline finishes — the card must not vanish.

---

## F3 — call stops never force their code open

**Where:** `Canvas/components/nodes/useNodeCode.ts` (outside the walkthrough folder):

```ts
const walkthroughCodeOpen = useWalkthroughStore(
  (s) => s.phase === "playing" && s.codeOpenNodeId === (nodeType === "call" && targetKey ? targetKey : nodeId),
);
```

**Wrong:** the executor stores `codeOpenNodeId = action.nodeId`, and for a call stop
the action's nodeId is the **call node's own id** (that is what the backend/mock puts
in the visit list). But this selector compares against `targetKey` (the target
function's id) for call nodes → never equal → the Monaco view is not forced open for
call stops. Same class of mismatch threatens the highlight: the hook receives
`nodeId={data.nodeId ?? ""}` (the call node id) while `highlight.nodeId` is also the
call node id — that pair is consistent; only the `codeOpenNodeId` comparison is
inverted.

**Fix:** compare against the node's own id always:
`s.codeOpenNodeId === nodeId`. Do NOT special-case calls here — the walkthrough
always addresses canvas nodes by their own id. (The `useCode` fetch below it already
maps call → targetKey for fetching content; leave that alone.)

**Prove:** manual with the fix-01 mock on a class containing a call stop: when the
tour reaches the call stop's first block, the call node's code view opens and
highlights. Also verify `nodeStartLine` used for mapping comes from
`codeData?.position?.line_no` (the target's position for calls — that is correct,
because the block line numbers are the target's lines too).

---

## F4 — one malformed NDJSON line kills the whole stream

**Where:** `source/httpSource.ts`, `JSON.parse(trimmed)` (twice: loop + tail).

**Wrong:** `JSON.parse` throws on a bad line, the exception leaves the read loop,
and the run dies — the plan (frontend/02) says log and continue, like Eregna's
widget.

**Fix:** wrap each `JSON.parse` in try/catch; on failure
`console.warn("[walkthrough] bad frame line", line)` and `continue` (or skip the
tail). Everything else unchanged.

**Prove:** vitest: feed the parsing helper a stream chunk containing
`good\nGARBAGE\ngood` (extract the line-splitting into a testable function if
needed) — both good frames arrive.

---

## F5 — panToNode can retry forever

**Where:** `executor/useStepExecutor.ts`, `panToNode` re-queues itself with
`requestAnimationFrame` whenever the node has no measured width.

**Wrong:** if the node never mounts (failed injection, user closed the tab, node
removed), this loops at 60 fps forever.

**Fix:** add an attempt counter parameter, default 0; bail at ~60 attempts
(`if (attempts > 60) return;`). Also bail early when
`useWalkthroughStore.getState().phase !== "playing"`.

**Prove:** code inspection + manual: exit the tour during a step transition; devtools
performance tab shows no persistent rAF loop.

---

## F6 — user-pan detection also fires on the tour's own pans

**Where:** `Canvas/components/CanvasView.tsx`, the added `onMoveStart` callback sets
`userInteracted = true` whenever the viewport starts moving while playing.

**Wrong:** ReactFlow fires `onMoveStart` for **programmatic** moves too (the
executor's own `setCenter`). Today this is masked because `next()`/`prev()` reset the
flag, but it makes the flag meaningless within a step and will fight future
auto-play.

**Fix:** ReactFlow passes the triggering event as the first argument:
`onMoveStart: (event, viewport) => ...`. Only set the flag when `event` is truthy
(user gesture — mouse/touch/wheel); programmatic moves pass `null`/`undefined`.
**Verify this against the installed @xyflow/react version** (open
`node_modules/@xyflow/react/dist/esm/index.d.ts` and check the `OnMoveStart` type)
before relying on it; if the event is always defined in this version, fall back to a
flag the executor sets around its own `setCenter` calls ("expect programmatic move
for 600 ms").

**Prove:** manual: during a step, do not touch the canvas; click Next repeatedly —
every step still auto-pans (meaning the tour's own pans did not poison the flag),
then pan by hand mid-step and confirm re-centering stops until the next step.

---

## F7 — Launcher polish (stale estimate, missing confirm)

**Where:** `components/Launcher.tsx`.

Three small ones:

1. The estimate is manual and goes stale silently: it is not cleared when
   `selectedNode` or `depth` changes. Fix: `useEffect` that resets
   `estimate/estimateError` when `selectedNode?.id` or `depth` changes, and
   (optionally, better) auto-fetches with a 300 ms debounce — the plan calls for a
   live estimate.
2. Overwriting a finished tour asks no confirmation: the guard skips
   `phase === "ready"`. Fix: confirm whenever `session != null` (any existing tour),
   i.e. replace the phase list check with `useWalkthroughStore.getState().session`.
3. `start()` resets state without restoring a stale `savedView` (if the user
   generated a new tour while a previous one was exited-but-not-discarded, the old
   snapshot is silently dropped — acceptable, but call `discard()` first in ALL
   overwrite paths so the restore happens; today only the confirm path discards).

**Prove:** manual: finish a tour → change nothing → press Generate → you get a
confirm. Change depth → the old estimate line disappears until re-estimated.

---

## F8 — decide the mock default consciously

**Where:** `source/index.ts` — mock is the default unless `VITE_WALKTHROUGH_MOCK` is
`"0"`/`"false"`.

Not a bug, but a trap: a production build with no env var ships mock mode. Keep
mock-by-default for now (backend isn't wired to a real provider yet), but add a
one-line startup log: `console.info("[walkthrough] source:", useMock ? "mock" : "http")`
so nobody debugs the wrong stack again. Revisit before any deploy.
