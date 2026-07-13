# Harness 03 — Confirmation, Depth, and the Real Max Depth

Every expensive operation passes one gate: estimate → confirm → run. This doc
covers the gate itself, how the depth knob works (agent suggests, user decides,
backend clamps), and the WOQL query that finds a subtree's *real* maximum depth.

## The gate

```
tool is a query tool                  → run (no gate — zero LLM calls)
estimate.over_cap                     → refuse with a human-readable message
                                        ("~64 stops at depth 3 — try depth 1")
confirmation == "always"              → confirm
confirmation == "over_threshold"
    and estimate.llm_calls > LIMIT    → confirm          (LIMIT ≈ 15)
otherwise                             → run
```

The policy lives in **one middleware** (`EstimateConfirmMiddleware`), not in each
tool. **Why:** tools declare *what they cost* (`estimate()` — pure code, instant);
the harness decides *whether to ask*. One place to tune, one place to test, and no
tool can forget the gate.

## Confirmation = LangGraph `interrupt()`

The middleware wraps task-tool execution:

1. run the tool's `estimate(args)` — deterministic arithmetic on the plan;
2. patch it onto the tool part (`state: awaiting_confirmation`, estimate + knobs);
3. call `interrupt({tool_call_id, estimate, knobs})` — the run suspends, the HTTP
   stream stays open, the conversation status flips.

`POST /conversations/{id}/decision` resumes with
`Command(resume={decision, overrides})`:

- **approve** → `overrides` (e.g. the user changed depth 3 → 1) merge into the tool
  args, then the tool runs;
- **cancel** → the middleware returns a `"declined by user"` tool result — the
  model sees it as an ordinary result and answers gracefully; the turn continues.

**Why interrupt instead of a custom pause.** It is the framework's supported
human-in-the-loop mechanism: suspension, checkpoint, resume-with-payload all come
for free, and it nests correctly in LangSmith traces. A hand-rolled pause would
re-implement all three.

## The depth knob — three parties, clear roles

| Party | Role | Why |
|---|---|---|
| **Agent** | *suggests* `depth` from the user's words ("quick look" → 0–1, "in detail" / "everything" → 2–3; default 1) and passes it in the tool args | it read the intent; a good prefill saves the user a click |
| **User** | *decides* on the confirm card — the knob is prefilled with the suggestion, its max set by the backend | it's their money and their time |
| **Backend** | *clamps*: `depth = min(requested, subtree_max_depth, HARD_MAX)` on both estimate and run | never trust either the model or the client with a cost bound |

`HARD_MAX = 5` (was 3 in the MVP request schema). The visit cap (`VISIT_CAP = 40`
in `app/walkthrough/traversal.py`) stays the real cost guard — a depth-5 request on
a huge tree still comes back `over_cap`. Depth bounds the shape; the cap bounds the
bill.

## Real max depth — the WOQL probe

**Problem.** Offering a depth-5 slider on a subtree that is only 2 deep is a lie:
levels 3–5 change nothing and the user can't know that. The UI (and the clamp)
should use the subtree's *actual* depth when it is smaller than the hard cap.

**Decision: a bounded exists-probe, one tiny query per level.**

```python
# app/walkthrough/traversal.py (or repo helper) — reuses the pagination plan's
# path machinery: build_path_field_name(...) over the SAME edge vocabulary the
# traversal loader walks (folder/file children + function_children,
# class_children, call_children, and the group edges — groups are transparent).
async def subtree_max_depth(repos, node_id: str, hard_cap: int = 5) -> int:
    for d in range(1, hard_cap + 1):
        found = await repos.…  # WOQL: path(node_id, (edge|edge|…){d,d}, v:x), limit 1
        if not found:
            return d - 1
    return hard_cap
```

**Why a probe and not one clever query.** WOQL path expressions support bounded
repetition `{n,m}` on a grouped choice (verified approach in
`plan/project-children-pagination/03-terminusdb-path-and-depth.md`), but they don't
cheaply return "the longest path length". Five `limit 1` exists-checks are bounded,
each is index-friendly, and the loop stops early on shallow trees — the common
case. If `{n,m}` turns out not to be supported on a parenthesized choice in our
TerminusDB version (the pagination plan flags this as *verify on install*), the
fallback is already written: `load_traversal_graph` walks the subtree anyway; count
its BFS levels. Same signature, slower, correct.

**Where the value flows:**

```
estimate response  {…, max_depth: 3}   → confirm card sets the knob's max
walkthrough run    clamp(requested)    → backend never runs deeper than real max
```

Cache per `(node_id, commit_id)` if it ever shows up in traces; don't build the
cache first.

## Verbosity — the second knob (from the user's words, not a slider)

"Give me a quick summary" and "explain it thoroughly" should produce different
tours without new pipeline machinery. The agent distills a `verbosity` arg
(`"quick" | "normal" | "detailed"`, default `"normal"`) alongside `user_query`
(context/03). The walkthrough tool maps it to a **prompt slot** in the intro and
block-text prompts only:

- `quick` → "keep each stop to 1–2 sentences; name what matters, skip mechanics"
- `detailed` → "explain each block thoroughly, including why the code needs it"

**Why an enum and not free text.** Greppable in traces, testable in evals, and it
can't smuggle instructions that fight the grounding rules. It does **not** change
the plan, the estimate, or the stop list — narration bends, structure doesn't
(same rule that keeps `user_query` out of the block planner). It is shown on the
confirm card next to depth, so the user can correct a wrong guess.
