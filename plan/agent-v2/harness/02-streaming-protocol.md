# Harness 02 — Streaming Protocol (multi-doc patches)

The wire between backend and frontend. This generalizes the walkthrough's proven
NDJSON patch protocol from one document to many, and adds one op (`append`) for
token streaming. The frontend plan will build against exactly this contract.

## What we already have (and why we keep the shape)

`app/walkthrough/patcher.py` today: a Pydantic **mirror** of the session, typed
helper methods (`set_intro`, `add_block`, …) that emit JSON-Patch ops, apply them
to the mirror, and stream them as NDJSON frames (`hello` / `patch` / `end`).

**Why keep it.** The mirror guarantees stored state and streamed state cannot
diverge — the same object the patches describe is the object we persist. That
guarantee held in the MVP; v2 needs it twice (conversation + artifacts), not
something new.

## Decision: many documents on one stream

A conversation run streams **the conversation doc** plus **one doc per task-tool
artifact** (e.g. a walkthrough session), over the same HTTP response. Every frame
names its doc.

```
{"kind":"open","doc":"conv/42","snapshot":{...conversation so far...}}
{"kind":"patch","doc":"conv/42","seq":0,"ops":[{"op":"add","path":"/messages/-","value":{...assistant msg, parts:[]}}]}
{"kind":"patch","doc":"conv/42","seq":1,"ops":[{"op":"add","path":"/messages/5/parts/-","value":{"type":"reasoning","origin":"native","text":""}}]}
{"kind":"patch","doc":"conv/42","seq":2,"ops":[{"op":"append","path":"/messages/5/parts/0/text","value":"User attached payments/ and wants"}]}
{"kind":"patch","doc":"conv/42","seq":7,"ops":[{"op":"add","path":"/messages/5/parts/-","value":{"type":"tool","tool":"walkthrough","state":{"status":"estimating"},...}}]}
{"kind":"open","doc":"walkthrough_session/ab12","snapshot":{...initial session incl. visit_list...}}
{"kind":"patch","doc":"walkthrough_session/ab12","seq":0,"ops":[...exactly today's walkthrough patches...]}
{"kind":"patch","doc":"conv/42","seq":8,"ops":[{"op":"replace","path":"/messages/5/parts/2/state/progress","value":{"done":3,"total":12,"label":"charge (3/12)"}}]}
{"kind":"close","doc":"walkthrough_session/ab12","status":"complete"}
{"kind":"close","doc":"conv/42","status":"idle"}
```

**Why one stream, not one per doc.** One connection = one ordering = no client-side
race between "tool finished" and "artifact finished". The frontend keeps a mirror
registry (`docId → {snapshot, lastSeq}`) and one reducer; a second connection would
force cross-stream synchronization for zero benefit.

Rules:

- **`open` carries a full snapshot**, then `patch` frames with a per-doc monotonic
  `seq`, then one terminal `close` per doc. The walkthrough's protocol-1 frames map
  1:1 (`hello`→`open`, `end`→`close`) — the tool's inner patch stream is reused
  byte-for-byte.
- **One new op: `append`** — string concatenation at a path. Chat text and reasoning
  stream token by token; sending the whole growing string per token is O(n²) bytes.
  The frontend reducer handles `append` in a pre-pass, then delegates standard ops
  to its JSON-Patch library. Artifact docs keep writing whole values (structured
  outputs arrive whole) — nothing inside them uses `append`.
- **Helpers only, never hand-written paths** (unchanged MVP rule). The conversation
  patcher exposes: `add_message`, `add_part`, `append_text(part, delta)`,
  `set_tool_state`, `set_tool_progress`, `set_tool_result`, `set_status`,
  `finalize_message(metadata)`.
- **`seq` per doc enables reconnect later**: a client can send `lastSeq` per open
  doc and the server replays from the persisted mirror. Not built now; costs
  nothing to leave room for.

## Patcher v2 (`app/agent/harness/patcher.py`)

Same class shape as the walkthrough `Patcher`, with two changes:

1. **A `doc` field on every frame**, and one mirror per doc (the conversation
   patcher and each tool's artifact patcher share the emit function, not the
   mirror).
2. **The `append` op** in the mirror-apply step (plain string concat before
   `jsonpatch` handles the rest).

The walkthrough tool receives a patcher pointed at its own
`walkthrough_session/<id>` doc — its internal helper calls don't change at all.

## The stream adapter — LangGraph events → patches

The only module that knows LangGraph's event shapes. If the framework's stream
format shifts on upgrade, one file changes and the wire doesn't.

| LangGraph stream event | Patch helper |
|---|---|
| reasoning delta (native channel or provider summary — normalized here, harness/04) | open a `reasoning` part on first delta; `append_text` after; settle on channel close |
| model content token | `append_text` on the current `text` part (pre-tool status line and final answer are both plain text) |
| tool call assembled on the AI message | `add_part(tool, status: "pending")` |
| estimate computed (EstimateConfirm middleware) | `set_tool_state(awaiting_confirmation, estimate, knobs)` |
| `interrupt()` raised | conversation `status` → `awaiting_confirmation` |
| tool execution starts | `set_tool_state(running)` |
| custom event from inside a tool (progress tick) | `set_tool_progress` — task tools also patch their own artifact doc directly |
| tool result returned | `set_tool_result` (compact summary + artifact ref + degraded flag); status `completed` / `error` |
| graph end | `finalize_message` (stop_reason, usage → metadata), persist, `close` conv doc |

**Why an adapter table instead of scattering.** Every mapping is greppable, every
mapping is testable with a recorded event fixture, and the framework never leaks
into components that render or persist.

## Progress labels are code, not LLM output

`set_tool_progress({done, total, label})` — the label ("charge (3/12)") is set by
tool code from the plan it is executing. The liveliest text in the UI costs zero
tokens and can never hallucinate. (Same rule as the MVP's step labels.)

## Transport

NDJSON on the response of `POST /conversations/{id}/messages`, exactly like
`/walkthroughs/run` today — `app/walkthrough/transport.py`'s `ndjson_response`
pattern is reused. While a run is `awaiting_confirmation` the stream stays open and
idle; the decision endpoint releases it (single-process assumption, fine now; a
task registry is the seam if that changes).
