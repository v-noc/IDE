# Harness 01 — The Agent Loop

One conversational loop, built on LangGraph's prebuilt agent. This doc explains
what a turn is, what the framework owns, what we own, and every guard around the
loop.

## Decision: use `create_agent`, don't hand-roll the loop

**Why.** The model↔tools cycle, tool-call parsing, retries on the transport level,
human-in-the-loop interrupts, checkpointing, and LangSmith span nesting are all
solved problems in LangGraph. Hand-rolling them is double work and double bugs —
the user's rule for this project is "use LangChain/LangGraph tools, don't do double
work". What the framework does *not* know about is our parts model and our wire
protocol — so that is exactly (and only) what we build: middleware for per-turn
behavior, and a stream adapter for the wire (harness/02).

**Version note.** `pyproject.toml` already has `langgraph>=1.2.9` and
`langchain>=0.3`. The middleware-style `create_agent` API is the LangChain 1.x
surface — on install, pin `langchain>=1.0` and verify the import path
(`langchain.agents.create_agent`). If we end up on the older prebuilt
(`langgraph.prebuilt.create_react_agent`), the same design holds: middleware
becomes pre/post hooks on the graph; nothing else in this plan changes.

## What a turn is

A **turn** = one user message → one agent invocation → one assistant message,
built part by part on the stream.

```python
# app/agent/harness/loop.py
agent = create_agent(
    model=build_agent_model(),            # via app/agent/llm/providers.resolve_llm
    tools=registry.langchain_tools(),     # generated from ToolSpecs (tools/01)
    middleware=[
        ProjectContextMiddleware(),   # system prompt: <project> header, every turn (context/03)
        NodeEnrichmentMiddleware(),   # node_ref parts → <attached_node> blocks (context/03)
        EstimateConfirmMiddleware(),  # task tools: estimate → interrupt() (harness/03)
        LimitsMiddleware(),           # max model calls per turn
    ],
    checkpointer=MemorySaver(),       # required by interrupt(); thread_id = conversation_id
)
```

`build_agent_model()` reuses the existing provider machinery: `resolve_llm()` from
`app/agent/llm/providers.py` gives provider + model + api key; `CALL_PARAMS` in
`app/agent/llm/structured.py` gains an `"agent"` entry (temperature, no completion
cap — the no-cap lesson from the MVP applies to the orchestrator too, since
reasoning models spend caps on hidden thinking first).

## One turn, step by step

```
POST /conversations/{id}/messages
  1. persist the user message (parts as sent — never rewritten)
  2. open the assistant message on the stream (patch: add_message)
  3. inputs = history.build(conversation)          ← deterministic, code only
  4. async for event in agent.astream(inputs,
         config={thread_id: conv_id, recursion_limit: sized to the step cap},
         stream_mode=["messages", "updates", "custom"]):
         stream_adapter maps event → patch helpers  ← harness/02 has the full table
  5. if the run raised interrupt():                 ← a tool needs confirmation
         conversation.status = "awaiting_confirmation"
         the HTTP stream stays open, idle
  6. on graph end: finalize the assistant message
     (stop_reason + usage + model_id into metadata), persist, close the doc

POST /conversations/{id}/decision
  agent.astream(Command(resume={decision, overrides}), same thread_id)
  → the adapter keeps mapping onto the same open stream
```

**Decision: the checkpointer is resume mechanics, not the source of truth.**
`MemorySaver` (in-process) is enough because the HTTP stream stays open across the
confirmation pause — the resume always happens in the same process. The durable
record is the conversation document in TerminusDB (data-model/02). If we ever need
cross-process resume, a TerminusDB-backed checkpointer is the seam; nothing else
changes.

## Thinking vs answer — native reasoning, not forced narration

*(Revised — harness/04 has the full design.)* The model is **not** prompted to
perform visible thinking. Instead:

- models with a native reasoning channel stream it (raw deltas or provider
  summaries, per the capability registry in harness/04) into a `reasoning` part —
  the collapsible thinking row, sized by the **effort** setting;
- before tool calls, a soft prompt rule asks for **one short plain sentence**
  ("I'll tour `charge` at depth 1") — an ordinary `text` part, the user-visible
  status line before each tool call or next task;
- models with no reasoning channel simply show no thinking row — no fake CoT.

**Why.** Forcing prose thinking makes reasoning models think twice (pay for the
hidden channel, then narrate a performance of it) and drifts toward theater. This
is the shape OpenCode, Codex, and Claude Code all landed on: surface the native
artifact, keep communication separate and short.

## History construction (`history.py`) — deterministic, in code

How stored parts become model messages. This is context engineering for the loop
itself, so the rules are explicit:

| Stored part | In the model's history |
|---|---|
| `text` (user/assistant) | plain content, verbatim — user words are never rewritten |
| `node_ref`, current turn | replaced by its full `<attached_node>` block (context/03) |
| `node_ref`, past turns | collapses to a one-line `<node …/>` card — the neighborhood is only fresh once, and re-sending it every turn would multiply cost for stale data |
| `tool` part | native tool-call + tool-result message pair; the result is the **compact summary only**, never the artifact payload — this is what keeps 30-turn conversations affordable |
| `reasoning` parts of past turns | **dropped** — never replayed across turns (harness/04); within a turn's tool loop, provider thinking-block requirements are the LangChain integration's job |
| `decision` parts | folded into the tool result ("user approved with depth 2" / "declined by user") |

Compaction (rolling summary of old turns) is deferred; this one module is the seam.
Compact tool results are what make deferring safe.

## Guards — all code-side

| Guard | Where | Behavior |
|---|---|---|
| Max steps per turn | `LimitsMiddleware` (~12 model calls) + `recursion_limit` | turn ends with `stop_reason: "max_steps"` and an honest closing sentence |
| Node ids | args validation in the tool layer | the model may only pass node ids that appeared in this conversation's `node_ref` parts or prior tool results. With search skipped in this build, attached nodes are the *only* source — fabricated ids are impossible by construction. |
| Tool arg validation | Pydantic on the tool's input schema | invalid args → error tool-result, the model corrects next step; second failure → the agent answers in plain text instead |
| Failed tool | never aborts the turn | tool part state `error`, result carries the reason, the model explains. Fatal only: DB or model unreachable. |
| Cancellation | `POST /cancel` → service cancels the `astream` task | tools cancel cooperatively between items; artifact status `aborted`; the assistant message closes with `stop_reason: "cancelled"` |
| Concurrent runs | one active run per conversation | second message while running → 409, same pattern as the walkthrough service's `_active_runs` |

**Why every guard is code.** The MVP's core lesson: small models follow structure
when the structure is enforced outside them. Nothing above depends on the model
behaving; the model only ever picks *which* validated action to take next.
