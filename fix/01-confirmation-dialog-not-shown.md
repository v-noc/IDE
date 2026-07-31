# Confirmation dialog not shown for walkthrough tool

## Problem

Ran `walkthrough` on `main` with depth 2. Expected the estimate/confirm dialog,
but the tool auto-ran (part went `pending` → `running` with no
`awaiting_confirmation` state and no `interrupt`).

## Root cause

The dialog is gated by `needs_confirmation` in
`src/backend/app/agent/tools/base.py:143`:

```python
def needs_confirmation(spec: ToolSpec, estimate: ToolEstimate, limit: int) -> bool:
    if estimate.over_cap:
        return False  # refuse path, not confirm
    if spec.confirmation == "always":
        return True
    if spec.confirmation == "never":
        return False
    # over_threshold
    return estimate.llm_calls > limit
```

The walkthrough spec uses `confirmation="over_threshold"`
(`walkthrough_tool.py:262`), and `limit` is `AGENT_AUTO_RUN_LIMIT`
(`src/backend/app/config/settings.py:40`), which defaults to **15**.

The estimate for this run was **exactly 15 LLM calls** (visible in the tool
result: `'llm_calls': 15`). The check is strict: `15 > 15` → `False` → no
dialog, tool auto-ran.

## All conditions where the dialog is NOT shown

1. `spec.confirmation == "never"` — dialog never appears.
2. `estimate.over_cap` is true — the tool is *refused* outright
   (`confirm.py:77`), no dialog; the model gets a "try smaller depth" message.
3. `spec.confirmation == "over_threshold"` and
   `estimate.llm_calls <= AGENT_AUTO_RUN_LIMIT` — auto-run. **← this run (15 ≤ 15)**
4. `spec.handler.estimate(...)` raises — the tool errors out before any
   confirmation (`confirm.py:67`).

This matches the plan (`plan/agent-v2/harness/03-confirmation-and-depth.md:15`
says `estimate.llm_calls > LIMIT → confirm`), so the code is behaving as
designed — the surprise is that a depth-2 tour on this sample project lands
exactly on the boundary.

## Why the threshold condition exists at all

`confirmation` is a **per-tool policy knob** with three values
(`never | over_threshold | always`, `base.py:52`), taken from the plan. The
idea behind `over_threshold` is standard cost gating: a 2-stop tour costing 3
LLM calls is nearly free, so asking "are you sure?" every time would be
nagging — only expensive runs should interrupt the user. That's why the plan
picked it for walkthrough (`plan/agent-v2/tools/02-walkthrough-tool.md:29` —
"small tours auto-run; big ones ask").

## Decision: walkthrough should be `always`

The threshold logic is fine as machinery, but it's the wrong policy for
*this* tool:

1. **The confirm card is not just a cost gate — it's the knobs editor.**
   `ConfirmCard` is where the user adjusts `depth` (with the detected max) and
   `verbosity` before the run. With `over_threshold`, small tours can never be
   tuned — they just fire.
2. **"Cheap" is not fast.** This "auto-run-worthy" 15-call tour took ~2.4
   minutes of wall clock. The user should opt in to that wait.
3. **Predictability.** A dialog that appears only sometimes feels random —
   exactly what happened here (expected a dialog, got silence, then had to
   diff-debug why).

### Fix (one word)

`src/backend/app/agent/tools/walkthrough_tool.py:262`:

```python
WALKTHROUGH_SPEC = ToolSpec(
    ...
    confirmation="always",   # was "over_threshold"
    ...
)
```

Keep `over_threshold` + `AGENT_AUTO_RUN_LIMIT` in place — they're the right
default for the cheaper agent-v3 write tools (describe/document), where
auto-running tiny jobs is the point. Also update the tool description string
(it already promises "an estimate is shown for approval" — with `always`
that finally becomes true unconditionally).

### Test to add

```python
def test_walkthrough_always_confirms():
    estimate = ToolEstimate(items=1, llm_calls=1, label="1 stop", over_cap=False)
    assert needs_confirmation(WALKTHROUGH_SPEC, estimate, 15) is True
```

Also consider logging the decision in `EstimateConfirmMiddleware`
(`confirm.py:90`) — one `logger.info` with `llm_calls`, `limit`, and the
outcome (`auto_run` / `confirm` / `refuse`) makes this diagnosable from logs
instead of a stream dump.
