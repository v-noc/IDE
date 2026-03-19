"""Map validated API DTOs to domain models."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.api.v1.conversations.schemas.parts import TextPartIn
from app.core.model.conversation_domain import MessagePart, TextPart


def message_parts_to_domain(parts: list) -> list[MessagePart]:
    out: list[MessagePart] = []
    for p in parts:
        if isinstance(p, TextPartIn):
            out.append(TextPart(text=p.text))
        else:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported message part: {type(p).__name__}",
            )
    return out
