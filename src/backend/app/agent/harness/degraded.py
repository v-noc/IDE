from __future__ import annotations

from app.agent.schemas.conversation import Conversation
from app.agent.schemas.parts import ToolCompleted, ToolPart


def count_degraded_tools(conversation: Conversation, message_index: int) -> int:
    if message_index < 0 or message_index >= len(conversation.messages):
        return 0
    message = conversation.messages[message_index]
    count = 0
    for part in message.parts:
        if isinstance(part, ToolPart) and isinstance(part.state, ToolCompleted):
            if part.state.degraded:
                count += 1
            # Also honor result.degraded_count when present
            degraded_count = part.state.result.get("degraded_count")
            if isinstance(degraded_count, int) and degraded_count > 0:
                count = max(count, 1)
    return count
