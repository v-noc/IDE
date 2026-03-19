"""
API message parts.

Use a discriminated union when more than one `type` exists (see Pydantic docs).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TextPartIn(BaseModel):
    type: Literal["text"] = "text"
    text: str = Field(..., min_length=1, max_length=1_000_000)


# Alias so request models and OpenAPI stay stable when new part types ship.
MessagePartIn = TextPartIn
