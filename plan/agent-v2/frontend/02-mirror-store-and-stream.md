# Frontend 02 — Mirror Store and the Stream

One store holds every live document (the conversation, each artifact) as a mirror
of what the backend streams. Components never touch frames; they select from
mirrors. This is `applyFrame.ts` generalized from one doc to many, plus the
`append` op.

## The store

```ts
// store/useMirrorStore.ts  (zustand + devtools, house pattern)
interface MirrorEntry {
  snapshot: unknown;              // Conversation | WalkthroughSession | …
  lastSeq: number;
  status: "open" | "closed" | "error";
  error?: string;
}

interface MirrorState {
  docs: Record<string, MirrorEntry>;          // "conv/42", "walkthrough_session/ab12"
  openDoc(doc: string, snapshot: unknown): void;
  patchDoc(doc: string, seq: number, ops: Op[]): void;
  closeDoc(doc: string, status: string, error?: string): void;
  seedDoc(doc: string, snapshot: unknown): void;   // reload path: GET snapshot → closed mirror
}
```

**Why one generic store instead of a conversation store + an artifact store.**
The wire treats every doc identically (`open`/`patch`/`close`), so the client
should too: one reducer to test, one seq/gap policy, and a new artifact type costs
zero store code. Typing happens at the *selector* boundary — `selectConversation`,
`selectWalkthroughSession` — where a component asks for a doc it knows the shape
of. (Zustand selectors + `useShallow` keep re-renders scoped, same as everywhere
else in the dashboard.)

## Frame application — three cases, one pre-pass

```ts
// stream/applyFrame.ts
case "open":   docs[frame.doc] = { snapshot: frame.snapshot, lastSeq: -1, status: "open" }
case "patch":  // seq guard copied from today's applyFrame:
               //   seq <= lastSeq → drop (stale); gap → warn, apply anyway
               snapshot = applyOps(snapshot, frame.ops)
case "close":  status = frame.status === "error" ? "error" : "closed"
```

`applyOps` runs the **`append` pre-pass**: ops with `op: "append"` are turned into
a string concat at the path (read value, `+ delta`, write back), everything else
goes to `fast-json-patch` exactly as today. Structural sharing matters here:
today's `applyOpsToSession` does `structuredClone` of the whole session per frame —
fine for a walkthrough, wasteful for per-token appends on a long conversation.
The v2 apply clones **only the path being touched** (parent chain), so a token
append re-renders the one part subscribed to that path and nothing else.

**Why the client applies patches instead of receiving snapshots.** Same reason as
the MVP: the backend's mirror and the client's mirror are the same object by
construction; and patches are the only affordable shape for token streaming.

## The stream source

```ts
// stream/source.ts — reuses parseNdjsonChunk/parseNdjsonTail from httpSource
export async function streamMessage(convId, parts, signal): Promise<void>
  POST /conversations/{convId}/messages  { parts }
  read response.body reader → NDJSON lines → frames → buffer
```

**Decision: coalesce frames per animation tick.** Token-level `append` frames can
arrive faster than 60 Hz; dispatching each to the store forces layout thrash. The
source buffers parsed frames and flushes the buffer to `useMirrorStore` in a
`requestAnimationFrame` callback (or on `close`). One rAF flush = one store
update = one render pass, and streaming still *looks* per-token because the tick
is 16 ms. This is the standard practice in chat UIs (Vercel AI SDK does the same
throttling client-side).

## The hooks

```ts
useRunStream(conversationId)
  send(parts)        → streamMessage(...); sets run status "running"
  stop()             → POST /cancel + AbortController on the fetch
  status             ← derived from the conversation mirror's `status` field
                       (idle | running | awaiting_confirmation | error)

useDecision()
  decide(toolCallId, decision, overrides?) → POST /conversations/{id}/decision
  // the stream is already open; the resumed frames just keep arriving

useConversations(projectId)
  list()             → GET /conversations           (summaries, F4 sidebar list)
  load(id)           → GET /conversations/{id}      → seedDoc("conv/"+id, snapshot)
```

**Why `send` and `decide` are separate hooks.** They hit different endpoints with
different lifecycles: `send` owns a fetch-stream for the whole run; `decide` is a
fire-and-forget POST whose *effects* arrive on the stream that `send` already
holds. Mixing them into one hook invites holding the decision until the stream
ends — the exact deadlock the design avoids.

## Reload (the honesty test for the whole store)

1. `load(id)` seeds `conv/{id}` from the persisted snapshot (`status: "closed"`).
2. The thread renders from the mirror — identically to how it rendered live,
   because parts are the persistence unit (data-model/02). No "replay" mode
   exists; there is nothing to replay.
3. When a rendered `ToolPart` carries an `ArtifactRef`, the artifact renderer
   lazily fetches `GET /conversations/{id}/artifacts/{doc}` and seeds that mirror
   (07).
4. If the conversation was `awaiting_confirmation`, the confirm card renders from
   the tool part's stored state and `useDecision` still works — the backend keeps
   the interrupted run resumable while the process lives; if it died, decide()
   returns 409 and the card shows "this run expired, ask again".

## Error surfaces

| Failure | UI |
|---|---|
| frame parse error / patch gap | console.warn + keep going (today's behavior) — a gap self-heals on reload |
| stream drops mid-run | run status → error; thread shows a quiet inline row "connection lost — reload to see where it got to"; no toast storm |
| `close` with `status: "error"` | the message's metadata.error renders as an inline error part; conversation stays usable |
| fetch rejected (backend down) | sonner toast — the one genuinely fatal case |
