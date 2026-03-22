"""Conversation metadata HTTP API (Phase 4).

TerminusDB @id values often contain `/` (e.g. ConversationSchema/uuid), which breaks
path segments. Resource ids are passed as query parameters instead.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.agent.conversation_store import ConversationStore
from app.api.v1.conversations.deps import get_conversation_store
from app.api.v1.conversations.params import ConversationIdQuery
from app.api.v1.conversations.schemas import (
    ConversationMetaResponse,
    CreateConversationRequest,
    PaginatedItems,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: CreateConversationRequest,
    store: ConversationStore = Depends(get_conversation_store),
) -> ConversationMetaResponse:
    cid = await store.create_conversation(body.title, body.description)
    meta = await store.get_conversation_metadata(cid)
    if meta is None:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Conversation created but not readable",
        )
    return ConversationMetaResponse(
        id=meta.id,
        title=meta.title,
        description=meta.description,
        message_count=meta.message_count,
        has_active_task=meta.has_active_task,
        created_at=meta.created_at,
        updated_at=meta.updated_at,
        metadata={},
    )


@router.get("")
async def list_conversations(
    limit: int = Query(default=50, ge=1, le=200),
    cursor: str | None = None,
    store: ConversationStore = Depends(get_conversation_store),
) -> PaginatedItems:
    items = await store.list_conversations(limit=limit + 1, cursor=cursor)
    has_more = len(items) > limit
    page = items[:limit]
    next_cursor = page[-1].id if has_more and page else None
    return PaginatedItems(
        items=[
            ConversationMetaResponse(
                id=s.id,
                title=s.title,
                description=s.description,
                message_count=s.message_count,
                has_active_task=s.has_active_task,
                created_at=s.created_at,
                updated_at=s.updated_at,
                metadata={},
            )
            for s in page
        ],
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.get("/meta")
async def get_conversation(
    conversation_id: ConversationIdQuery,
    store: ConversationStore = Depends(get_conversation_store),
) -> ConversationMetaResponse:
    meta = await store.get_conversation_metadata(conversation_id)
    if meta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    full = await store.get_conversation(conversation_id)
    md = full.metadata if full else {}
    return ConversationMetaResponse(
        id=meta.id,
        title=meta.title,
        description=meta.description,
        message_count=meta.message_count,
        has_active_task=meta.has_active_task,
        created_at=meta.created_at,
        updated_at=meta.updated_at,
        metadata=md,
    )


@router.delete("")
async def delete_conversation(
    conversation_id: ConversationIdQuery,
) -> None:
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented for this storage backend",
    )
