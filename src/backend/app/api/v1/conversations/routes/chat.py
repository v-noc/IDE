"""Conversation messages and agent chat HTTP API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.agent.conversation_store import ConversationStore
from app.agent.streaming.wire import conversation_message_to_wire
from app.agent.service.chat_service import ChatService
from app.api.dependencies import get_chat_service
from app.api.v1.conversations.deps import get_conversation_store
from app.api.v1.conversations.mappers import message_parts_to_domain
from app.api.v1.conversations.params import ConversationIdQuery
from app.api.v1.conversations.schemas import (
    PaginatedItems,
    PostMessageResponse,
    SendConversationMessageRequest,
)
from app.core.model.conversation_domain import ConversationMessage
from app.core.model.conversation_enums import MessageRole

router = APIRouter(prefix="/conversations", tags=["chat"])


@router.get("/messages")
async def list_messages(
    conversation_id: ConversationIdQuery,
    cursor: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    store: ConversationStore = Depends(get_conversation_store),
) -> PaginatedItems:
    meta = await store.get_conversation_metadata(conversation_id)
    if meta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    rows = await store.list_messages(
        conversation_id, cursor=cursor, limit=limit + 1
    )
    has_more = len(rows) > limit
    page = rows[:limit]
    next_c: int | None = None
    if has_more and page:
        next_c = page[-1].sequence + 1
    return PaginatedItems(
        items=[conversation_message_to_wire(m) for m in page],
        next_cursor=next_c,
        has_more=has_more,
    )


@router.post(
    "/messages",
    status_code=status.HTTP_202_ACCEPTED,
)
async def post_message(
    body: SendConversationMessageRequest,
    chat: ChatService = Depends(get_chat_service),
    store: ConversationStore = Depends(get_conversation_store),
) -> PostMessageResponse:
    cid = body.conversation_id
    meta = await store.get_conversation_metadata(cid)
    if meta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")

    domain_parts = message_parts_to_domain(body.parts)
    user_msg = ConversationMessage(
        id=str(uuid.uuid4()),
        role=MessageRole.USER,
        parts=domain_parts,
    )
    out = await chat.send_message(
        cid,
        user_msg,
        store=store,
        completion_params=body.generation,
        client_ref=body.client_ref,
    )
    return PostMessageResponse(
        message_id=out.get("message_id"),
        task_id=out["task_id"],
        conversation_id=out["conversation_id"],
        stream_id=out["stream_id"],
        client_ref=body.client_ref,
    )
