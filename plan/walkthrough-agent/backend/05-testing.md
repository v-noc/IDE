# 05 — Testing

The strategy in one line: **everything except prompt quality is testable without an
API key**, because the `fake` provider is a first-class registry member and the
pipeline is deterministic around the LLM.

## The fake provider (agent/llm/fake.py)

A LangChain-compatible chat model that returns canned structured outputs by
`call_type`:

- `intro` → `{reasoning: "...", intro: "Intro for <node name>."}` (name parsed from
  the prompt's `### node` section — proves context assembly end to end).
- `block_plan` → an even split within the bounds stated in the prompt (it reads
  `{min_blocks}`/`{max_blocks}` and the line range — proves the prompt carries them).
- `block_text` → `"Explains lines A–B of <name>."`

Two knobs, settable per test:

```python
FakeChatModel(call_type, fail_first_attempts=0, malformed=False)
```

`fail_first_attempts=1` → first response is invalid (out-of-range lines / broken
JSON), second is good — exercises the retry path. `fail_first_attempts=2` →
exercises the fallback path. This makes the failure policy (parent 05) a *tested
contract*, not a hope.

## Test pyramid

| Layer | Tests | LLM |
|---|---|---|
| **Unit: traversal** | order (calls before siblings), depth counting, groups-free, duplicate rule (full/contextual), recursion, gate + bounds, estimate arithmetic, over-cap | none |
| **Unit: validators** | every BlockPlan rule from parent 04 (bounds, containment, order, overlap, coverage) with minimal failing inputs; even-split fallback correctness | none |
| **Unit: patcher** | each helper emits expected ops; mirror after all ops == mirror mutated directly; seq monotonic; frame log round-trips | none |
| **Unit: prompts** | builders render all placeholders (no `{...}` left); bounds injected match the VisitNode; banned-content greps on templates | none |
| **Integration: pipeline** | full graph run on a small fixture project with `fake` provider: session completes, node_steps count matches visit list, degraded flags on induced failures, usage accumulates | fake |
| **Integration: routes** | httpx streaming client against the app (existing e2e patterns): hello/patch/end framing, 409 lock, 422 over-cap, disconnect → aborted session | fake |
| **Integration: persistence** | doc created → appended → finalized; crash mid-run (kill the task) leaves truthful partial | fake |
| **Manual/eval: prompt quality** | CLI harness on real nodes with the real provider; fixture re-run diffs (parent 07) | real |

The fixture project for integration tests: a tiny real project checked into
`tests/fixtures/` (a few files with a class, functions, a call across files, a
one-liner, a recursive function) — indexed once in the test DB. Every traversal edge
case in parent 03 appears in it by construction.

## The CLI harness (cli.py)

```
uv run python -m app.walkthrough.cli <project_id> <node_id> <depth>
    [--provider vercel|openai|custom|fake]   # overrides settings for this run only
    [--out session.json]                     # dump the final session
    [--frames frames.ndjson]                 # dump the patcher frame log
```

Prints the tour as readable text (stop headers, block ranges, texts) plus a summary
line (calls made, retries, fallbacks, tokens, wall-clock). This is where prompt
iteration happens (backend build stage before the frontend swap), with the model that
will actually run — GLM/Kimi via the gateway, not a stand-in.

`--frames` output **is** the frontend fixture format (frontend 02): recording a real
run for the frontend's mock mode is running the CLI with two flags. That closes the
loop: backend CLI runs → frontend fixtures → player regression harness.

## What we consciously don't test

- Prose quality by assertion (length bounds and banned-phrase greps only; quality is
  the human fixture-diff loop from parent 07).
- Provider outages/rate limits beyond "surface as honest error end-frame" (one test
  with a raising fake).
- Load/concurrency beyond the per-project lock test — single-user IDE.
