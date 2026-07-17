# Verbosity knob (Quick / Normal / Detailed) doesn't change narration length

## Problem

The walkthrough confirm card's Detail control (Quick / Normal / Detailed) and
the `verbosity` tool arg change nothing about the tour. Narration comes out
the same length whatever the user picks. The knob renders, the agent passes
the value, the result dict even reports it back — but the text is identical.

## Root cause 1: `verbosity` never reaches the pipeline

`agent/tools/walkthrough_tool.py` accepts it and carries it everywhere
*except* into the run:

- accepted: `WalkthroughArgs.verbosity` (`walkthrough_tool.py:40`)
- shown on the confirm card: `knobs={"verbosity": args.verbosity}` (`:71`)
- echoed into the outcome: `result={"verbosity": args.verbosity}` (`:132`, `:245`)
- **dropped**: the `RunRequest` built for the pipeline
  (`walkthrough_tool.py:162-166`) is

  ```python
  request = RunRequest(
      project_id=project.id,
      node_id=args.node_id,
      depth=args.depth,
  )
  ```

  and `RunRequest` (`walkthrough/schemas.py:18`) has no `verbosity` field to
  begin with — `project_id`, `node_id`, `depth`, nothing else. From there,
  `new_session(request, …)` embeds the request in the session and
  `run_pipeline` (`walkthrough/pipeline.py:47`) reads only
  `session.request.project_id` / `.depth`. The knob is decorative end to end.

## Root cause 2: the prompts hardcode the length anyway

Even if the value arrived, there is no slot for it. All three narration
prompts pin their length in a numbered rule (`walkthrough/prompts.py`):

| Prompt | Line | Hardcoded rule |
|---|---|---|
| `INTRO_FULL_SYSTEM` | `prompts.py:38` | "Aim for 2-4 sentences. First sentence: …" |
| `INTRO_CONTEXTUAL_SYSTEM` | `prompts.py:62` | "Aim for 2-3 sentences, in the caller's context: …" |
| `BLOCK_TEXT_SYSTEM` | `prompts.py:115` | "Aim for 2-4 sentences. Explain what the block does…" |

`BLOCK_PLAN_SYSTEM` also carries counts (`{min_blocks}-{max_blocks}`) but that
is **correct and stays** — the settled v2 decision is that verbosity is a
narration-side lens and never reaches the block planner: the tour's structure
(stops, blocks) must not change with wordiness, only the popup text does.

## Fix

Thread the value through the existing seams, then swap the hardcoded clause
for an injected one. Five small changes:

**1. `walkthrough/schemas.py` — `RunRequest` gains the field.**

```python
class RunRequest(BaseModel):
    project_id: str
    node_id: str
    depth: int = Field(ge=0, le=5)
    verbosity: Literal["quick", "normal", "detailed"] = "normal"
```

Defaulted, so the old direct HTTP route (`walkthrough/routes.py`) keeps
working unchanged.

**2. `walkthrough_tool.py:162` — pass it.** `verbosity=args.verbosity` in the
`RunRequest(...)` call. (The estimate/knob/result plumbing already exists.)

**3. `walkthrough/pipeline.py` — expose it to the graph.** Add
`"verbosity": session.request.verbosity` to `config["configurable"]` (and to
`metadata` next to `depth`, so traces show which lens a run used).

**4. `walkthrough/orchestrator.py` — hand it to the renderers.** The two call
sites (`orchestrator.py:78` `intro_system_prompt(ctx)`, `:194`
`block_text_system_prompt(text_ctx)`) pass it through:
`intro_system_prompt(ctx, verbosity)` — the contextual-vs-full branch inside
`intro_system_prompt` already exists, so one parameter covers both intro
prompts.

**5. `walkthrough/prompts.py` — replace the hardcoded clause with a
`{length_rule}` slot** filled from one table. The current texts become the
`quick` presets **verbatim** — today's behavior is the floor, nothing regresses:

```python
LENGTH_RULES: dict[str, dict[str, str]] = {
    "intro_full": {
        "quick":    "Aim for 2-4 sentences.",
        "normal":   "Write two short paragraphs (3-5 sentences each), "
                    "separated by a blank line.",
        "detailed": "Write two to three paragraphs. Go deeper on the node's "
                    "role, its collaborators, and why it exists — still from "
                    "the outside, never into block-level mechanics.",
    },
    "intro_contextual": {
        "quick":    "Aim for 2-3 sentences,",
        "normal":   "Write one full paragraph (4-6 sentences),",
        "detailed": "Write two paragraphs — the call itself, then how it "
                    "fits the caller's flow —",
    },
    "block_text": {
        "quick":    "Aim for 2-4 sentences.",
        "normal":   "Write two short paragraphs: what the block does, then "
                    "why the code needs it.",
        "detailed": "Write two to three paragraphs. Cover the branches and "
                    "error paths visible in the block — depth over padding; "
                    "never narrate line by line.",
    },
}
```

Rule 1 of each template becomes e.g.
`"1. {length_rule} First sentence: what this {node_type} IS and what it is for."`
(the sentence-1 contract, grounding rules, and bans all stay outside the slot —
only the length clause moves). The renderers pick
`LENGTH_RULES[key][verbosity]` and format it in; `verbosity` defaults to
`"normal"` at every signature so direct callers keep working.

**Bump `PROMPT_VERSION`** (`walkthrough/schemas.py`) — sessions stamp it, and
this changes all three narration prompts.

## Behavior change, intentional

Default runs get longer: `normal` (the tool default and the UI's default
segment) now means two paragraphs, where today's output was 2-4 sentences.
That's the point of the fix — today's length is what `quick` is for. Detailed
runs also cost more output tokens per stop; the estimate counts LLM *calls*,
which don't change, so no estimate math moves.

## Same seam, same bug: `user_query`

The intent lens has the identical gap — accepted (`walkthrough_tool.py:33`),
echoed in results (`:131`, `:244`), absent from `RunRequest`, absent from the
prompts (no `<user_intent>` section exists in `prompts.py` at all). Fix it in
the same pass while the seam is open: field on `RunRequest`, through
`configurable`, rendered as a labeled section in the intro/block *user*
prompts with the settled rules (emphasis only, never skip, grounding senior —
plan/agent-v2, harness docs). Kept out of this doc's scope but it should not
ship as a second round-trip through these five files.

## Tests to add

- **Prompt unit tests**: render each of the three system prompts at each
  verbosity → assert the injected clause is present and the hardcoded one is
  gone; assert `BLOCK_PLAN_SYSTEM` output is byte-identical across verbosity
  (the planner must stay blind to it).
- **Tool test**: `WalkthroughArgs(verbosity="detailed")` → the `RunRequest`
  inside the bridged run carries `"detailed"` and it appears in
  `config["configurable"]`.
- **Schema test**: `RunRequest(project_id=…, node_id=…, depth=1)` still
  validates (default `"normal"`) — the old route contract holds.
