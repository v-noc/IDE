from __future__ import annotations

import re

from app.agent.schemas.conversation import Conversation
from app.agent.schemas.parts import TextPart


_TITLE_MAX = 60


def title_from_user_text(text: str) -> str:
    """Deterministic cheap title — no LLM required."""
    cleaned = " ".join((text or "").strip().split())
    if not cleaned:
        return "New conversation"
    # Drop leading polite fluff
    cleaned = re.sub(
        r"^(please|hey|hi|hello)[,!.\s]+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip() or cleaned
    if len(cleaned) <= _TITLE_MAX:
        return cleaned
    cut = cleaned[:_TITLE_MAX].rsplit(" ", 1)[0]
    return (cut or cleaned[:_TITLE_MAX]).rstrip(".,;:") + "…"


def first_user_text(conversation: Conversation) -> str:
    for message in conversation.messages:
        if message.role != "user":
            continue
        for part in message.parts:
            if isinstance(part, TextPart) and part.text.strip():
                return part.text
    return ""


def maybe_title(conversation: Conversation) -> str | None:
    """Return a title if the conversation still needs one."""
    if (conversation.title or "").strip():
        return None
    text = first_user_text(conversation)
    if not text:
        return None
    return title_from_user_text(text)
