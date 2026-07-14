# Walkthrough data never appears in the chat

## Was it generated?

**Yes, completely.** The stream dump proves it end to end:

- `open` frame for `walkthrough_session/d57d5b8965d6` with the full visit list
  (8 nodes, depth 2)
- 28 patches (`seq 0–27`) streaming every stop: intro texts and code-block
  narrations for all 8 `node_steps`
- `close` frame with `status: "complete"`
- tool result: `'status': 'complete', 'stops': 8, 'degraded_count': 0`

The frames rode the same SSE stream the conversation uses, so the frontend
received them and `useMirrorStore` built the full session under
`docs["walkthrough_session/d57d5b8965d6"]`. The data was sitting in the store
the whole time — nothing ever rendered it.

## Why you only saw "running"

Two independent causes:

### Cause 1 (live view): artifact only renders in the `completed` branch

`ToolCard.tsx` mounts the artifact viewer exclusively inside
`state.status === "completed"`:

```tsx
{state.status === "completed" ? (
  <div className="space-y-2">
    ...
    {state.artifact
      ? renderArtifact(state.artifact.render, state.artifact.doc)
      : null}
  </div>
) : null}
```

The `ArtifactRef` (`{doc: "walkthrough_session/…", render: "walkthrough"}`)
only exists on the `ToolCompleted` state — and that state is never emitted
because `on_tool_completed` is dead code (**fix 02**). So the chain is:

```
tool part stuck at "running"
  → no ToolCompleted state
    → no state.artifact
      → renderArtifact never called
        → WalkthroughArtifact never mounts
          → session sits unused in useMirrorStore
```

**Fix 02 fixes this.** Once the completed state lands with its `ArtifactRef`,
`WalkthroughArtifact` mounts, `useWalkthroughBridge` copies the mirror doc
into `useWalkthroughStore`, and the existing player (PlayControls +
TourOutline) takes over. No frontend change needed for the live case.

Optional UX: while `running`, the walkthrough streams stop-by-stop — the
mirror doc is already growing. You could render the artifact in the `running`
branch too (the bridge already handles `entry.status === "open"` →
`generating`/`playing` phases), so the user watches stops appear instead of a
bare "Running…" line. That's polish, not the bug.

### Cause 2 (after reload): the artifact doc is ephemeral

Even with fix 02 applied, reload the page and the walkthrough is gone:

- Backend: `ConversationPatcher._patch` persists **only the conversation
  doc** (`patcher.py:257` — `if persist and doc == self.doc_id`). Artifact
  docs opened via `open_doc` are never persisted anywhere; there is no
  walkthrough-session repo, table, or GET endpoint (verified — `new_session`
  output lives only in the in-memory `Patcher.mirror`).
- Frontend: on reload, `useMirrorStore` starts empty; the persisted
  conversation still has the `ToolCompleted` part with its `ArtifactRef`, so
  `WalkthroughArtifact` mounts — but `docs[artifact.doc]` is `undefined` and
  the bridge renders an empty player.

So the `ArtifactRef` becomes a dangling pointer after every reload.

**Fix:** persist the final artifact snapshot at close time and let the
frontend re-seed on demand. `useMirrorStore.seedDoc` already exists and is
built for exactly this (sets a doc with `status: "closed"`).

1. Backend — in `ConversationPatcher.close_doc` (or in the walkthrough tool
   after the `end` frame), save the mirror's final JSON keyed by doc id.
   Simplest storage that fits the current stack: an `artifacts` field on the
   conversation document itself (`dict[doc_id, snapshot]`), since
   `on_persist` already saves the whole conversation; a separate artifact repo
   is the cleaner long-term shape if sessions get large.
2. API — return the artifacts with the conversation snapshot (or add
   `GET /agent/artifacts/{doc}`).
3. Frontend — when `WalkthroughArtifact` mounts and
   `useMirrorStore.docs[doc]` is missing, call `seedDoc(doc, snapshot)` with
   the fetched/embedded snapshot.

## Test to add

- Frontend: render `ToolCard` with a `completed` state carrying an
  `ArtifactRef` whose doc exists in the mirror store → walkthrough player
  renders; with the doc missing → seed path is triggered (no empty player).
- Backend: after a bridged walkthrough run, the persisted conversation (or
  artifact store) contains the closed session snapshot under the same doc id
  as the `ToolCompleted.artifact.doc`.
