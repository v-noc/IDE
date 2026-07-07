# 05 — Orchestration (LangGraph)

How the pipeline is wired as a LangGraph graph, and why a graph at all when the flow is
deterministic.

## Why LangGraph for a deterministic pipeline

Honest answer: a plain `for` loop over the visit list would work for MVP. We use
LangGraph anyway, for three practical reasons:

1. **State in one place.** The graph state object is the single source of truth while
   generating; every stage reads and writes it. No threading six variables through
   function calls.
2. **Retry/fallback as topology.** "Validate → retry once → fallback" is a conditional
   edge, visible in the graph drawing, instead of try/except spaghetti.
3. **Room to grow without rewiring.** Free-form questions later add a planner node in
   front; pipelining (generate stop N+1 while N streams) is a concurrency change, not
   an architecture change.

What we do **not** use: agent executors, tool-calling loops, dynamic routing by the
model. The graph's edges are decided by code inspecting state — never by LLM output
choosing a route.

## Graph state

```python
class WalkthroughGraphState(TypedDict):
    session_id: str
    branch: str
    commit_id: str                   # pinned at run start; all code/doc reads use it
    visit_list: VisitList            # fixed input; never mutated
    contexts: dict[str, NodeContext] # prefetched code/docs/child lines per stop (06)
    cursor: int                      # index into visit_list.nodes
    current_plan: BlockPlan | None   # scratch: the active stop's block plan
    block_cursor: int                # scratch: which block is being explained
    node_steps: list[NodeSteps]      # accumulating output
    error_log: list[str]
    usage: TokenUsage
```

Two side channels are injected as config, not state, so the graph stays a pure state
machine: `patcher` (typed helpers that mutate the session mirror and stream JSON-Patch
frames — see 04) and `persist` (the TerminusDB session writer, fed from the same
mirror). Where the graph diagram below says "emit X", read "call the patch helper for
X, which emits a frame".

## The graph

```mermaid
flowchart TB
    START([start]) --> NEXT{"cursor < len(visit_list)?"}
    NEXT -- no --> DONE(["finish: persist status=complete\nemit done"])
    NEXT -- yes --> INTRO["intro\nLLM: narrator\nemit node_intro"]
    INTRO --> KIND{"stop kind?"}
    KIND -- "container / contextual" --> ADV["advance\nassemble NodeSteps\npersist append · emit node_done\ncursor += 1"]
    KIND -- "full code, lines < GATE" --> ONEBLOCK["single_block\nblocks = [whole body]\n(no LLM)"]
    KIND -- "full code, gated" --> PLAN["block_plan\nLLM: block planner"]
    PLAN --> VAL{"valid?"}
    VAL -- "no — attempt 1" --> PLANR["retry with\nvalidator message"]
    PLANR --> VAL2{"valid?"}
    VAL2 -- no --> FB["fallback\neven split (no LLM)\nlog to error_log"]
    VAL -- yes --> EMITP["emit block_plan"]
    VAL2 -- yes --> EMITP
    FB --> EMITP
    ONEBLOCK --> EXPL
    EMITP --> EXPL["explain_block\nLLM: explainer for blocks[block_cursor]\nemit block_text"]
    EXPL --> MORE{"more blocks?"}
    MORE -- yes --> EXPL
    MORE -- no --> ADV
    ADV --> NEXT
```

One iteration of the outer loop = one stop's micro-pipeline. Every diamond is a code
decision reading state; the three rectangles marked `LLM` are the only model calls.

## Node-by-node

### `intro`
- Builds the intro prompt from `contexts[node_id]` (exact contents in 06). Two prompt
  variants, chosen by code from `VisitNode.mode`:
  - **full / container** — describe the node from outside.
  - **contextual** — explain what this call does *for its caller* (inputs, result,
    why here), referencing `first_seen_order` ("covered at stop N") when it exists.
- One LLM call, schema: `{reasoning: str, intro: str}`.
- On parse/validation failure: one retry; then fallback `intro = node.description`,
  `degraded = True`. Either way the tour continues.
- Emits `node_intro` immediately — this is what makes generation feel alive.

### `block_plan`
- Only reached for full code stops past the gate. Prompt contains the numbered code
  (read at `commit_id`) and the computed bounds ("choose between 2 and 4 blocks").
- Schema: `BlockPlan` (`reasoning` first, then `blocks`).
- Validation per 04. First failure → retry **with the validator's message appended** —
  small models correct well when told exactly what was wrong ("block 2 ends at line 57
  but the function ends at line 52"). Second failure → deterministic even split.
- Emits `block_plan` so the outline grows sub-rows before any text exists.

### `explain_block`
- One LLM call per block — the smallest call in the system. Schema: `{text: str}`.
  The prompt includes the previous blocks' `focus` lines so block 3 doesn't re-explain
  block 1.
- Failure handling: one retry; then fallback `text = focus`, `degraded = True`.
- Emits `block_text`; loops via `block_cursor` until blocks are done.

### `advance`
- Assembles the finished `NodeSteps`, appends it to state, **persists it to the
  session document in TerminusDB**, emits `node_done`, bumps `cursor`. Pure code.
- Persisting per stop (not once at the end) means a crash or disconnect leaves a
  truthful partial session — replayable up to the last finished stop.

## Failure policy (uniform — memorize once)

```
every LLM call:  try → validate
                 fail 1 → retry once, appending the exact validator error
                 fail 2 → deterministic fallback + degraded flag + error_log entry
never:           abort the tour because of one bad call
fatal only:      DB/source unreachable, model auth/quota → persist status=error, SSE error
```

This is the small-model contract: assume every call *can* fail and make failure boring.

## Model configuration

- **One chat model for all three call types**, configurable id (GLM-4.7, Kimi 2.5,
  anything OpenAI-compatible) via LangChain `init_chat_model`. A per-call-type
  override is a config field we leave room for but build no UI for.
- `temperature 0.2` for block plans (structure should be stable), `0.5` for intros and
  block texts (prose can breathe).
- Structured output via `with_structured_output`, JSON mode preferred for these
  providers. Known provider quirks to guard against (documented in Eregna v2's fixes
  folder): disable parallel tool calls, avoid optional fields in strict schemas, and
  never let reasoning tokens leak into the JSON channel.
- `max_tokens` per call type: intro 300, block plan 400, block text 350. A runaway
  generation gets cut, fails validation, and lands in the normal retry path.

## Ordering and concurrency

MVP runs strictly sequential — simplest to reason about, and SSE order matches visit
order for free. Two later upgrades, both invisible to the frontend contract:

- **Pipelining:** run stop N+1's `intro` while stop N's blocks are explaining. Events
  per stop stay ordered; interleaving across stops is already legal for the store,
  which keys everything by `node_id`.
- **Batching block texts:** collapse the `explain_block` loop into one call per stop
  with an array schema — a cost cut, kept behind a flag until eval'd against
  per-block quality.
