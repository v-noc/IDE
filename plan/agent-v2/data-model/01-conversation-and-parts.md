# Data Model 01 — Conversation, Message, Parts

What a conversation *is*. Pydantic on the backend, mirrored in `types.ts` later,
discriminated on `type`. The shapes follow the practices of harnesses that have
already survived production — OpenCode and the Vercel AI SDK v5 — adapted to our
graph domain.

## Prior art, and what we take from it

| Practice | Who does it | What we take |
|---|---|---|
| Message = list of typed **parts**, not one string | OpenCode (`MessageV2.Part`), AI SDK v5 (`UIMessage.parts`) | the part union below; streaming, rendering, and persistence all operate on parts |
| Tool call as a part with a **state machine object** | OpenCode `ToolState` (`pending → running → completed/error`, each status with its own fields) | a nested `state` union instead of flat nullable fields — fields that only exist in one status can't leak into others |
| Model id, tokens, cost on the assistant message | OpenCode (`modelID`, `tokens`, `cost`) | grouped into **one `metadata` field** (Yared's call), so the part list stays purely about content |
| `type` as the discriminator name | both | `type`, not the MVP's `kind` — matches what the frontend ecosystem expects |

**Why copy proven shapes at all.** The data model is the hardest thing to change
later (persistence + wire + UI all depend on it). Harnesses like OpenCode already
paid for these lessons — e.g. flat tool fields (`result`, `error`, `progress` all
nullable side by side) rot into "which fields are valid in which state?" bugs;
their nested state union fixes it structurally.

## Top level

```python
class Conversation(BaseModel):
    id: str
    project_id: str
    title: str = ""                      # generated after the first turn (cheap call, Phase 4)
    created_at: datetime
    updated_at: datetime
    status: Literal["idle", "running", "awaiting_confirmation", "error"]
    messages: list[Message]
    schema_version: str                  # HARNESS_SCHEMA_VERSION


class Message(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    created_at: datetime
    parts: list[Part]
    metadata: MessageMetadata = MessageMetadata()
```

## `MessageMetadata` — everything that is *about* the message

```python
class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0            # reasoning models bill these; be honest about them
    cache_read_tokens: int = 0


class MessageMetadata(BaseModel):
    # assistant messages ────────────────────────────────
    model_id: str | None = None          # "vercel:zai/glm-4.7" — resolve_llm's model_id format
    prompt_version: str | None = None    # AGENT_PROMPT_VERSION at the time (prompts/01)
    effort: Literal["off", "low", "medium", "high"] | None = None
                                         # reasoning effort actually applied (harness/04)
    usage: TokenUsage | None = None
    cost_usd: float | None = None        # None when the provider gives no pricing
    duration_ms: int | None = None
    stop_reason: Literal["end_turn", "max_steps", "cancelled", "error"] | None = None
    error: str | None = None             # human-readable, only with stop_reason "error"
```

**Why one metadata object instead of top-level fields.** Three reasons.
(1) *Separation of audiences*: `parts` is what the conversation says; `metadata` is
bookkeeping about how it was produced. Renderers iterate parts and never touch
metadata; a usage panel reads metadata and never touches parts.
(2) *Cheap evolution*: adding `cost_usd` or a future `provider_request_id` is a new
optional field in one sub-model — no migration of the message shape, no wire
change.
(3) It matches where this data already lives in the MVP (`WalkthroughSession`
carries `model_id`, `usage`, `prompt_version` at the artifact level — same idea,
message level).

## The part union

```python
Part = Annotated[
    TextPart | NodeRefPart | ReasoningPart | ToolPart | DecisionPart,
    Field(discriminator="type"),
]
```

### User-side parts

```python
class TextPart(BaseModel):
    type: Literal["text"]
    text: str                            # streams via `append` on assistant messages


class NodeRefPart(BaseModel):            # a node dragged onto the composer
    type: Literal["node_ref"]
    node_id: str
    name: str
    qname: str | None
    node_type: str                       # folder | file | class | function | call


class DecisionPart(BaseModel):           # the user's reply to a confirmation card
    type: Literal["decision"]
    tool_call_id: str
    decision: Literal["approve", "cancel"]
    overrides: dict = {}                 # e.g. {"depth": 1} — the knobs they changed
```

`NodeRefPart` is how "the selected node" lives inside a chat: attaching a node is
just composing a message with a typed attachment. With search skipped in this
build, this part is the **only** source of node ids the agent has — which is the
whole anti-hallucination story (harness/01 guards).

`DecisionPart` is stored in the conversation even though the resume travels through
its own endpoint. **Why:** the transcript must be replayable — "the user approved
with depth 1" is part of what happened, and history.py folds it into the tool
result the model sees.

### Assistant-side parts

```python
class ReasoningPart(BaseModel):          # native model CoT, surfaced (harness/04)
    type: Literal["reasoning"]
    origin: Literal["native", "summary"] # raw deltas vs provider-generated summary
    text: str
    duration_ms: int | None = None       # settles when the channel closes — feeds
                                         # the "Thought for 3s" row


class ToolPart(BaseModel):
    type: Literal["tool"]
    tool_call_id: str
    tool: str                            # registry name, e.g. "walkthrough"
    state: ToolState                     # the state machine — see below
```

### `ToolState` — a union, one shape per status

```python
class ToolPending(BaseModel):
    status: Literal["pending"]
    input: dict                          # validated args

class ToolAwaitingConfirmation(BaseModel):
    status: Literal["awaiting_confirmation"]
    input: dict
    estimate: ToolEstimate               # items, llm_calls, label, over_cap (tools/01)
    knobs: dict                          # {"depth": {"value": 2, "max": 3}, "verbosity": "quick"}

class ToolRunning(BaseModel):
    status: Literal["running"]
    input: dict
    progress: ToolProgress | None        # {done, total, label} — set by CODE, patched live
    started_at: datetime

class ToolCompleted(BaseModel):
    status: Literal["completed"]
    input: dict
    result: dict                         # MODEL-FACING compact summary (goes into history)
    artifact: ArtifactRef | None         # USER-FACING rich doc (never enters history)
    degraded: bool = False               # any fallback fired inside the tool
    duration_ms: int

class ToolError(BaseModel):
    status: Literal["error"]
    input: dict
    error: str                           # includes "declined by user" for cancels
    duration_ms: int

ToolState = Annotated[..., Field(discriminator="status")]


class ArtifactRef(BaseModel):
    doc: str                             # "walkthrough_session/ab12"
    render: str                          # renderer hint: "walkthrough" (more later)
```

**Why `result` and `artifact` are separate fields.** One field per audience — the
harness-level version of the MVP's `focus`/`description` split. The model reads a
five-line JSON summary; the user gets the full artifact document rendered richly.
Artifact payloads never entering model history is what keeps long conversations
affordable.

## Versioning

- `HARNESS_SCHEMA_VERSION` on the conversation — bumped when part shapes change,
  same discipline as the walkthrough's `SCHEMA_VERSION`.
- `prompt_version` per assistant message (in metadata) and per artifact — the eval
  loop keys on it.
