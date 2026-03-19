"""Reusable FastAPI Query declarations for TerminusDB document ids (may contain `/`)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Query

ConversationIdQuery = Annotated[
    str,
    Query(
        ...,
        min_length=1,
        max_length=512,
        description="Full TerminusDB id (e.g. ConversationSchema/uuid). URL-encode `/` as %2F.",
    ),
]

TaskIdQuery = Annotated[
    str,
    Query(
        ...,
        min_length=1,
        max_length=512,
        description="Full task document id or in-memory task id. URL-encode `/` as %2F.",
    ),
]
