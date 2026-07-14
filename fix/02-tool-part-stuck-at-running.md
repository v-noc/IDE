# Tool part stuck at "running" after the run finishes

## Problem

The walkthrough completed (artifact doc closed with `status: complete`,
conversation `status` went back to `idle`, assistant metadata finalized), but
the tool card in the chat still shows **"running"** forever.

## Frontend or backend?

**Backend.** The frontend is faithful: `ToolCard.tsx` renders
`part.state.status` directly, and `applyFrame` just applies the patches it
receives. The stream dump proves no completion patch was ever sent:

- `seq 23` — tool part added with `state.status: "pending"`
- `seq 24` — `replace /messages/3/parts/1/state` → `"running"`
- …walkthrough doc streams and closes `complete`…
- `seq 26` — tool result appended **as text** (see fix 03)
- `seq 33` — message metadata finalized
- `seq 34` — conversation `status` → `idle`

There is no patch that ever moves `parts/1/state` to `completed`. The
conversation-level status and the per-part tool state are separate fields; only
the first one gets closed out today.

## Root cause

The completion callback exists but is dead code end to end:

1. `ToolServices.on_tool_completed` is declared
   (`src/backend/app/agent/tools/base.py:32`) but `run_agent_turn` and
   `resume_agent_turn` never pass it when building `ToolServices`
   (`src/backend/app/agent/harness/loop.py:135-144`, `:231-240`).
2. Nothing ever calls it anyway:
   - `EstimateConfirmMiddleware.awrap_tool_call` fires `on_tool_pending`,
     `on_awaiting_confirmation`, `on_tool_running`, `on_tool_error` — then just
     `return await handler(request)` (`confirm.py:136`) with no post-run hook.
   - `langchain_tools._run` (`base.py:129`) returns `str(outcome.result)` and
     drops the structured `ToolOutcome` (result dict, `ArtifactRef`,
     `degraded`) on the floor.
3. `ToolPartTracker.completed` (`tool_tracker.py:73`) is fully implemented —
   it has zero callers.

So after `running`, the part's state machine simply has no exit transition.

## Fix

Three small changes; the middleware stays the single owner of the tool
lifecycle.

### 1. `tools/base.py` — let the structured outcome ride on the ToolMessage

LangChain's `content_and_artifact` response format sends `content` to the
model and keeps `artifact` for downstream code. Return the `ToolOutcome` as
the artifact for task tools:

```python
        async def _run(
            __spec: ToolSpec = spec,
            **kwargs: Any,
        ) -> Any:
            services = get_tool_services()
            args = __spec.input_model.model_validate(kwargs)
            if __spec.kind == "query":
                result = await __spec.handler.run(args, services)
                return str(result)

            outcome: ToolOutcome = await __spec.handler.run(args, services)
            return str(outcome.result), outcome

        tools.append(
            StructuredTool.from_function(
                coroutine=_run,
                name=spec.name,
                description=spec.description,
                args_schema=spec.input_model,
                response_format=(
                    "content_and_artifact" if spec.kind == "task" else "content"
                ),
            ),
        )
```

(Verified against installed versions: langchain 1.3.13 / langchain-core 1.4.9
— `StructuredTool.from_function` accepts `response_format`, and
`ToolMessage.artifact` exists.)

### 2. `harness/confirm.py` — dispatch completion after the handler returns

`handler(request)` returns `ToolMessage | Command`. After it resolves, report
completed/error with a measured duration (replaces the bare
`return await handler(request)` at the end of `awrap_tool_call`):

```python
        if services.on_tool_running is not None:
            await services.on_tool_running(call_id, args.model_dump())

        started = time.monotonic()
        try:
            result = await handler(request)
        except Exception as exc:
            if services.on_tool_error is not None:
                await services.on_tool_error(call_id, str(exc))
            raise
        duration_ms = int((time.monotonic() - started) * 1000)

        if isinstance(result, ToolMessage):
            if result.status == "error":
                if services.on_tool_error is not None:
                    await services.on_tool_error(call_id, str(result.content))
            elif services.on_tool_completed is not None:
                outcome = (
                    result.artifact
                    if isinstance(result.artifact, ToolOutcome)
                    else None
                )
                await services.on_tool_completed(
                    call_id,
                    input_args=args.model_dump(),
                    result=outcome.result if outcome else {"content": str(result.content)},
                    artifact=outcome.artifact if outcome else None,
                    degraded=outcome.degraded if outcome else False,
                    duration_ms=duration_ms,
                )
        return result
```

Needs `import time` and `ToolOutcome` added to the existing
`from app.agent.tools.base import ...` import.

Note `on_tool_running` now also passes `args.model_dump()` — that fixes a
second bug visible at `seq 24`: `tracker.running()` is called with no args
(`loop.py:129-130`), so `ToolRunning(input={})` **wipes the input** the
pending state had. The frontend loses the tool's input while it runs.

### 3. `harness/loop.py` — wire the callback (both entry points)

In `run_agent_turn` *and* `resume_agent_turn`:

```python
    async def on_running(call_id, input_args=None):
        await tracker.running(call_id, input_args)

    async def on_completed(
        call_id, *, input_args, result, artifact=None, degraded=False, duration_ms=0,
    ):
        await tracker.completed(
            call_id,
            input_args=input_args,
            result=result,
            artifact=artifact,
            degraded=degraded,
            duration_ms=duration_ms,
        )

    services = ToolServices(
        ...,
        on_tool_running=on_running,
        on_tool_completed=on_completed,   # ← currently missing
        ...
    )
```

## Related: resume will duplicate tool parts

Not hit yet (the dialog never showed — see fix 01), but it will bite once
confirmation works: on approve, `resume_agent_turn` builds a **fresh**
`ToolPartTracker` with an empty `_parts` map, and LangGraph re-executes
`awrap_tool_call` from the top, so `on_tool_pending` fires again →
`tracker.pending` unconditionally `add_part`s (`tool_tracker.py:32`) → a
second, duplicate tool part in the message.

`ConversationPatcher.find_tool_part` (`patcher.py:260`) exists for exactly
this and is currently unused. Make the tracker rebind instead of blindly
appending — in `pending` (and as a fallback in `running`/`completed`/`error`):

```python
    def _index_for(self, tool_call_id: str) -> int | None:
        index = self._parts.get(tool_call_id)
        if index is not None:
            return index
        found = self.patcher.find_tool_part(self.assistant_index, tool_call_id)
        if found is None:
            return None
        self._parts[tool_call_id] = found[0]
        return found[0]
```

`pending` should use it to update-in-place instead of `add_part` when the
part already exists.

## Tests to add

- Tracker: `pending → running → completed` leaves the part in `completed`
  with the original input preserved (catches both the missing transition and
  the input wipe).
- Tracker: `pending` called twice with the same `tool_call_id` does not add a
  second part (resume path).
- Middleware: fake handler returning a `ToolMessage` with a `ToolOutcome`
  artifact → `on_tool_completed` called with the outcome's result/artifact;
  `ToolMessage(status="error")` → `on_tool_error`.
