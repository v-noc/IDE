from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PaginatedItems(BaseModel):
    items: list[Any] = Field(default_factory=list)
    next_cursor: str | int | None = None
    has_more: bool = False
