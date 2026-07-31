# Harness 04 — Reasoning and Effort (native CoT, not forced CoT)

Revision of the thinking design. The first draft *forced* visible thinking: the
prompt ordered the model to write 1–3 "analysis" sentences before tool calls, and
the adapter classified them into an analysis part. This doc replaces that with
what OpenCode, Codex, and Claude Code converged on: **use the model's native
reasoning channel when it has one, size it with an effort setting, and show the
user what the provider exposes** — extracted raw or summarized.

## Why the forced version was worse

- It made every model pay prose tokens for theater — even reasoning models that
  had *already thought* in their hidden channel thought twice (the exact
  double-thinking the MVP's 08 doc warned about inside tools).
- Prompt-manufactured "thinking" is written to be seen, so it drifts toward
  performance ("I will now carefully…") instead of being a truthful trace.
- Every serious harness dropped this approach: Claude Code streams real extended
  thinking; Codex streams the Responses API's reasoning summaries; OpenCode has a
  first-class `reasoning` part fed by whatever the provider exposes. Fighting the
  ecosystem here buys nothing.

## Prior art (what exactly we're adopting)

| Harness | Native CoT handling | Effort |
|---|---|---|
| Claude Code | Anthropic extended thinking, interleaved with tool use; thinking blocks rendered collapsed | thinking budget (tokens), user-settable |
| Codex CLI | OpenAI Responses reasoning; **summaries** streamed between actions (raw CoT is hidden by the provider) | `reasoning_effort: low/medium/high`, user-settable |
| OpenCode | `reasoning` message part; populated from `reasoning_content` deltas on providers that expose them | per-model provider options |

Common shape: *the harness never asks the model to narrate its thinking; it
surfaces whatever reasoning artifact the provider emits, and exposes one effort
knob that scales it.*

## The capability registry

`ProviderSpec` (in `app/agent/llm/providers.py`) gains a per-model reasoning
capability — this is data, verified once per provider, not runtime detection:

```python
class ReasoningCaps(BaseModel):
    channel: Literal["exposed", "summary", "none"]
        # exposed  → raw deltas stream (GLM-4.7 / Kimi reasoning_content,
        #            Anthropic thinking blocks)
        # summary  → provider emits summaries, raw CoT hidden (OpenAI Responses)
        # none     → plain model, no reasoning channel
    effort_param: Literal["reasoning_effort", "budget_tokens", "thinking_flag", None]
    always_on: bool = False              # o-series style: can't be disabled, only sized
```

Effort is one enum everywhere: **`off | low | medium | high`**, mapped per
provider by the registry (exact values verified on install, like every provider
detail):

| effort | `reasoning_effort` models | budget-token models | flag-style (GLM/Kimi) |
|---|---|---|---|
| off | not sent (`minimal` if `always_on`) | thinking disabled | `thinking: disabled` |
| low | `low` | ~4k | enabled |
| medium | `medium` | ~12k | enabled |
| high | `high` | ~32k | enabled |

**Why one enum and not raw budgets in the API.** The frontend and the settings
file shouldn't know that one provider counts tokens and another takes a string.
`overrides_for()` in `providers.py` already does exactly this translation for
`gpt-5` (`reasoning_effort: low` via `extra_body`) — this promotes that ad-hoc
entry into the mechanism.

## Where effort is set (three layers, later wins)

```
settings.AGENT_REASONING_EFFORT = "medium"        # deployment default
conversation-level override                        # frontend knob (frontend/05)
per-message option: POST …/messages {parts, options: {effort}}
```

The applied effort is stamped into `MessageMetadata.effort` — the record shows
what actually ran, same honesty as `model_id`. Task-tool micro-calls are **not**
touched by this knob: block plans and narration keep their small-model, low-
temperature contract (05/08 of the MVP); effort governs the orchestrator only.

## What the user sees — two channels, cleanly split

1. **The reasoning row** (`reasoning` part, data-model/01) — filled only from the
   native channel:
   - `channel: exposed` → deltas stream in live (`append` ops), origin `"native"`;
   - `channel: summary` → summary text as it arrives, origin `"summary"` (the UI
     labels it as a summary — honesty about what it is);
   - `channel: none` → **no reasoning part at all**. No fake thinking; the
     frontend's anti-fake rule (frontend/04) now has a backend guarantee behind it.
2. **The pre-tool status line** — one short plain **text part** before tool
   calls: *"I'll tour `charge` at depth 1 — it's small."* This is the "small
   summary before the tool call / next task". It is ordinary assistant text
   (rendered as such, not collapsed), kept by a soft prompt rule — one sentence,
   plain words, no ids. It replaces the old forced analysis entirely.

**Why both.** The reasoning row is a *trace* (variable length, collapsible,
skippable); the status line is *communication* (always short, always visible).
Merging them was the original design's mistake: one artifact can't be both a
faithful trace and a guaranteed-short summary.

## Adapter changes (the only code that touches provider shapes)

The stream adapter (harness/02) gains one event family:

| Event | Patch |
|---|---|
| reasoning delta on a message chunk (`additional_kwargs.reasoning_content`, Anthropic `thinking` content block, Responses summary delta — normalized here) | open a `reasoning` part on first delta; `append_text` after |
| reasoning channel closes (first content/tool-call token) | settle the part (duration recorded on it) |

Extraction points differ per provider (`langchain-openai` and
`langchain-anthropic` each surface them differently); the adapter normalizes all
of them to the same part. **One file knows this** — the rule from harness/02,
unchanged.

History rules (harness/01) extend naturally: reasoning parts are **never
replayed into later turns' history** (same as the old analysis parts — and for
`summary` providers the raw CoT was never ours to replay anyway). Within a
single turn's tool loop, provider requirements about passing thinking blocks
back are handled by the LangChain integration, not by us.

## Token and cost honesty

`TokenUsage.reasoning_tokens` (already in the metadata schema) is where the
effort knob's cost shows up. The frontend's metadata footer displays it when
non-zero — the user who turns effort to `high` sees what it costs, which is the
whole feedback loop that makes an effort knob meaningful instead of magical.

## Failure and degradation

| Case | Behavior |
|---|---|
| provider rejects the effort param (wrong model, gateway strips it) | log once, run without it — reasoning params are enhancement, never a precondition |
| reasoning deltas malformed / partial | the part keeps what arrived; settle on channel close; never block content on reasoning |
| `always_on` model with effort `off` | send the minimal supported effort; stamp what was actually sent in metadata |
