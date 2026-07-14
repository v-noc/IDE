# Raw tool result leaks into the assistant text part

## Problem

The chat text shows the tool's raw result dict inline, glued between the
assistant's sentences:

> I'll generate a step-by-step walkthrough… `{'session_id':
> 'walkthrough_session/d57d5b8965d6', 'status': 'complete', 'stops': 8, …}`
> Walkthrough created and ready.

In the stream dump this is `seq 26`: a single `append` op that writes the
whole `str(outcome.result)` repr into `/messages/3/parts/0/text` — the same
text part the LLM was streaming into.

## Root cause

`_stream_agent` (`src/backend/app/agent/harness/loop.py:64`) streams with
`stream_mode="messages"`, which yields **every** message produced in the
graph — AI token chunks *and* `ToolMessage`s (tool results). Every item is
forwarded to `StreamAdapter.on_message_chunk`
(`src/backend/app/agent/harness/stream_adapter.py:80`), which extracts
`message.content` as text and appends it to the current text part. A
`ToolMessage`'s content is the stringified tool result, so it lands in the
visible chat text.

Tool results already reach the UI through their own channel (the tool part /
artifact doc), so the adapter should never render them as prose.

## Fix

Early-return on tool messages at the top of `on_message_chunk`:

```python
from langchain_core.messages import ToolMessage

    async def on_message_chunk(self, message: Any) -> None:
        if isinstance(message, ToolMessage):
            return
        ...
```

`ToolMessageChunk` subclasses `ToolMessage` (verified on langchain-core
1.4.9), so one isinstance check covers both. Usage extraction is unaffected —
token usage only arrives on AI chunks.

If you'd rather not import langchain types there, `getattr(message, "type",
"") == "tool"` works too, but the isinstance is safer (chunk types have
different `type` strings).

## Test to add

Feed the adapter an AI chunk, then a `ToolMessage(content="{'x': 1}",
tool_call_id="c1")`, then another AI chunk — the text part must contain only
the two AI chunks' text.
