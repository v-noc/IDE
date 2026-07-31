# Tools 02 — The Walkthrough Tool

The MVP pipeline becomes the first task tool. The wrapper is thin and boring on
purpose: everything hard (traversal, contexts, prompts, validation, fallbacks,
per-node streaming) already works in `app/walkthrough/` and is **not touched**.

## The spec

```python
# app/agent/tools/walkthrough_tool.py

class WalkthroughArgs(BaseModel):
    node_id: str = Field(description="The attached node to tour from. Only use ids "
                                     "the user attached to this conversation.")
    depth: int = Field(1, ge=0, le=5, description="How many levels below the start "
                                     "node. Suggest from the user's wording; the user "
                                     "confirms before the tour runs.")
    user_query: str = Field("", description="The user's goal, one plain sentence in "
                                     "their words. Empty if they expressed no angle.")
    verbosity: Literal["quick", "normal", "detailed"] = "normal"

SPEC = ToolSpec(
    name="walkthrough",
    description="Generate a guided, step-by-step tour of a code node the user "
                "attached. Streams a playable walkthrough; the user sees it as a "
                "tour outline. Costs LLM calls — an estimate is shown for approval.",
    input_model=WalkthroughArgs,
    kind="task",
    confirmation="over_threshold",       # small tours auto-run; big ones ask
    render="walkthrough",
    handler=WalkthroughTool(),
)
```

## `estimate()` — delegate, then decorate

```
1. subtree_max = subtree_max_depth(repos, node_id, hard_cap=5)    (harness/03 WOQL probe)
2. depth       = clamp(args.depth, 0, subtree_max)
3. delegate to the existing WalkthroughService.estimate(node_id, depth)
   → node_count, step_estimate, llm_call_estimate, over_cap (VISIT_CAP unchanged)
4. return ToolEstimate(
       items=node_count, llm_calls=llm_call_estimate,
       label=f"{node_count} stops · ~{llm_call_estimate} LLM calls",
       over_cap=over_cap,
       knobs={"depth": {"value": depth, "max": subtree_max},
              "verbosity": args.verbosity})
```

The knobs dict is what the confirm card renders: the depth slider prefilled with
the agent's suggestion, capped at the subtree's real max — the MVP's depth picker,
relocated to the moment it matters, with an honest ceiling.

## `run()` — the existing service, pointed at an artifact doc

```
1. re-clamp depth from the approved args (overrides merged by the middleware)
2. session = the existing pipeline run, with its Patcher pointed at
   doc "walkthrough_session/<id>" on the shared conversation stream
   (patcher v2 — the tool's internal helper calls are unchanged)
3. inject <user_intent> + the verbosity rule into intro/block-text prompts only
   (context/03; block plan never sees either)
4. persist the session document per node_done (a WalkthroughSessionRepo appears
   here — the MVP never persisted sessions; v2 must, because ArtifactRef points
   at a doc that has to be loadable after reload)
5. return ToolOutcome(
       result={"session_id": …, "stops": 12, "steps": 31, "llm_calls": 29,
               "degraded_count": 1, "status": "complete"},
       artifact=ArtifactRef(doc=f"walkthrough_session/{id}", render="walkthrough"),
       degraded=bool(degraded_count))
```

**Why the result summary is exactly this.** It is everything the agent needs to
close the turn honestly ("done — 12 stops, one fell back to its stored
description") and nothing that would bloat history. The artifact carries the rest.

## What changes inside `app/walkthrough/` (the complete list)

| Change | Why |
|---|---|
| `RunRequest.depth` bound `le=3` → `le=5` | new hard max; `VISIT_CAP` still guards cost (harness/03) |
| accept `user_query` + `verbosity` → prompt slots in intro/block-text | the customization hook; prompt-side only |
| `Patcher` constructed with a doc id + shared emit | patcher v2 compatibility; helper API unchanged |
| `subtree_max_depth` helper (next to `traversal.py`'s cap logic) | the WOQL probe lives with its siblings |
| `WalkthroughSession` persisted via a repo | artifacts must survive reload |
| store `user_query`, `verbosity` on the session | evals need to see the lens that was applied |

Everything else — traversal order, visit modes, block planning, validators,
fallbacks, degraded flags, token accounting — untouched.

## The agent's job around this tool (prompt contract, prompts/01)

- pick `node_id` from an attached node — never invent one; if nothing is attached
  and the user asks for a tour, ask them to attach a node (one sentence, not a
  form);
- distill `user_query` / `verbosity` / suggested `depth` per the rules in
  context/03;
- relay the estimate honestly; when `over_cap`, suggest a smaller depth instead of
  retrying blindly;
- after the run: one-line outcome + degraded count if any — **no re-narration of
  the artifact** (the user can see it; repeating it costs tokens and drifts).

## Existing `/walkthroughs/*` routes

Kept working until the frontend switches to conversations (the frontend plan will
schedule that), then deprecated. The tool calls `WalkthroughService` directly —
same service both paths, so there is no behavior fork while both exist.
