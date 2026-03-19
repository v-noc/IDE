from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.agent.chat.completion_params import ChatCompletionParams
from app.api.v1.conversations.schemas.parts import TextPartIn


class CreateConversationRequest(BaseModel):
    title: str = Field(default="New conversation", min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)


class SendConversationMessageRequest(BaseModel):
    """
    Submit a user turn and schedule streamed assistant generation.

    `conversation_id` is the full TerminusDB document id (may contain `/`);
    clients should URL-encode it when passed as a query parameter elsewhere.
    """

    conversation_id: str = Field(
        ...,
        min_length=1,
        max_length=512,
        description="Full conversation document id, e.g. ConversationSchema/<uuid>",
    )
    role: Literal["user"] = "user"
    parts: list[TextPartIn] = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Ordered segments; schema uses `type` for forward-compatible unions.",
    )
    generation: ChatCompletionParams | None = Field(
        default=None,
        description="Optional per-request LLM overrides.",
    )
    client_ref: str | None = Field(
        default=None,
        max_length=128,
        description="Optional idempotency or correlation key for the client.",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Opaque envelope; not interpreted by the runner today.",
    )
