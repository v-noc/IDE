# "Play walkthrough" button does nothing (chat-generated tours)

## Problem

After the completion fixes, the walkthrough artifact renders in the chat with
"▶ Play walkthrough" and "N steps ready" — but clicking Play does nothing. No
error, no phase change, no camera movement. (Clicking a stop in the outline
does nothing either.)

## Root cause: the store's `tabId` is never set on the chat path

`play()` in `useWalkthroughStore.ts:191` silently bails without a tab:

```ts
void (async () => {
  const { tabId, session } = get();
  if (!tabId || !session) {
    set((state) => { state.preparing = false; });
    return;                       // ← silent bail, no feedback
  }
  await prepareTour(queryClient, tabId, session);
  ... phase = "playing" ...
})();
```

`tabId` identifies the canvas tab the tour plays in — `prepareTour` needs it
to materialize/expand the stops (`ensureOnCanvas(queryClient, tabId, …)`) and
`captureSavedView(tabId)` snapshots the camera for restore-on-exit.

The two entry paths differ:

- **v1 Launcher path** (`Launcher.tsx:85`): calls
  `start(req, activeTabId)` with `useTabStore`'s active tab — `tabId` is set,
  Play works.
- **v2 chat path** (`WalkthroughArtifact.tsx:35`, `useWalkthroughBridge`):
  copies the mirror doc into the store with
  `useWalkthroughStore.setState({ session, lastSeq, phase, error,
  playerSteps, cursor })` — **`tabId` is never included**, so it stays `null`
  from `initialState`.

So on the chat path: click Play → first guard passes (session + steps exist)
→ `preparing = true` → async block sees `tabId === null` → `preparing =
false` → return. The button flickers back to "▶ Play walkthrough". Exactly
"nothing happens".

`jumpTo()` has the identical guard (`useWalkthroughStore.ts:272`), which is
why outline clicks are dead too.

## Fix

Resolve the tab at **click time**, not at bridge time. The user may switch
canvas tabs between generation finishing and pressing Play, and the chat
overlay isn't tied to any tab — "play in the tab you're currently looking
at" matches the v1 semantics (`Launcher` used `activeTabId` too).

In `useWalkthroughStore.ts`, at the top of `play()` (and mirror the same in
`jumpTo()`):

```ts
import useTabStore from "@/features/Dashboard/store/useTabStore";

play() {
  const current = get();
  if (!current.session || current.playerSteps.length === 0 || current.preparing) {
    return;
  }

  // Chat-generated tours never went through start(req, tabId) —
  // fall back to whichever canvas tab the user is looking at.
  if (!current.tabId) {
    set((state) => {
      state.tabId = useTabStore.getState().activeTabId;
    });
  }
  ...
}
```

`activeTabId` defaults to `'root'` (`useTabStore.ts:41`) and is reassigned to
the root tab when a tab closes (`useTabStore.ts:70-71`), so the fallback is
always a live tab — the old `!tabId` bail then only guards the impossible
case.

Alternative considered: setting `tabId` inside `useWalkthroughBridge` when
seeding the store. Rejected — the bridge fires on every mirror-doc change
(including mid-generation patches), so it would pin the tour to whichever tab
happened to be active while the tool was still streaming, and it silently
goes stale if the user closes that tab before playing.

## Also: don't bail silently

The reason this took a debugging session instead of a glance: `play()`
swallows its failure. `prepareTour` already toasts when stops fail to load —
do the same on the bail path:

```ts
if (!tabId || !session) {
  toast.error("No canvas tab to play the walkthrough in");
  set((state) => { state.preparing = false; });
  return;
}
```

## Tests to add

- Store test: seed the store the way the bridge does (`setState` with a
  session, no `tabId`, no `start()` call), stub `useTabStore` with an active
  tab, call `play()` → phase becomes `"playing"`, `tabId` picked up from the
  tab store, cursor `0`.
- Store test: same seed but `jumpTo(stepId)` → same expectations at the
  jumped index.
