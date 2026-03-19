"""Conversation API DTOs (pagination, parts, requests, responses)."""

from app.api.v1.conversations.schemas.pagination import PaginatedItems
from app.api.v1.conversations.schemas.parts import MessagePartIn, TextPartIn
from app.api.v1.conversations.schemas.requests import (
    CreateConversationRequest,
    SendConversationMessageRequest,
)
from app.api.v1.conversations.schemas.responses import (
    ConversationMetaResponse,
    PostMessageResponse,
)
from app.api.v1.conversations.schemas.tasks import subtask_to_wire, task_to_wire

__all__ = [
    "ConversationMetaResponse",
    "CreateConversationRequest",
    "MessagePartIn",
    "PaginatedItems",
    "PostMessageResponse",
    "SendConversationMessageRequest",
    "TextPartIn",
    "subtask_to_wire",
    "task_to_wire",
]
