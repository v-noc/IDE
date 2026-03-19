"""Conversation and task HTTP API (Phase 4).

TerminusDB @id values often contain `/` (e.g. ConversationSchema/uuid), which breaks
path segments. Resource ids are passed as query parameters instead.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.agent.runner.executor import AgentExecutor
from app.agent.runner.task_manager import TaskManager
from app.agent.conversation_store import ConversationStore
from app.agent.realtime.wire import conversation_message_to_wire
from app.api.v1.conversations.deps import (
    get_agent_executor,
    get_conversation_repo,
    get_conversation_store,
    get_task_manager,
)
from app.api.v1.conversations.mappers import message_parts_to_domain
from app.api.v1.conversations.params import ConversationIdQuery, TaskIdQuery
from app.api.v1.conversations.schemas import (
    ConversationMetaResponse,
    CreateConversationRequest,
    PaginatedItems,
    PostMessageResponse,
    SendConversationMessageRequest,
    subtask_to_wire,
    task_to_wire,
)
from app.core.model.conversation_domain import ConversationMessage
from app.core.model.conversation_enums import MessageRole

router = APIRouter(prefix="/conversations", tags=["conversations"])

tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


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
    rows = await store.list_messages(conversation_id, cursor=cursor, limit=limit + 1)
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
    executor: AgentExecutor = Depends(get_agent_executor),
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
    out = await executor.handle_chat_message(
        cid,
        user_msg,
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


@router.get("/tasks")
async def list_conversation_tasks(
    conversation_id: ConversationIdQuery,
    cursor: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    repo=Depends(get_conversation_repo),
    store: ConversationStore = Depends(get_conversation_store),
) -> PaginatedItems:
    meta = await store.get_conversation_metadata(conversation_id)
    if meta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    tasks = await repo.list_tasks_for_conversation(
        conversation_id, limit=limit + 1, cursor=cursor
    )
    has_more = len(tasks) > limit
    page = tasks[:limit]
    next_c = cursor + len(page) if has_more else None
    return PaginatedItems(
        items=[task_to_wire(t) for t in page],
        next_cursor=next_c,
        has_more=has_more,
    )


@tasks_router.get("/detail")
async def get_task(
    task_id: TaskIdQuery,
    repo=Depends(get_conversation_repo),
    tm: TaskManager = Depends(get_task_manager),
):
    t = await repo.get_task(task_id)
    if t is not None:
        return task_to_wire(t)
    mem = tm.get_status(task_id)
    if mem is not None:
        return task_to_wire(mem)
    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")


@tasks_router.get("/subtasks")
async def list_subtasks(
    task_id: TaskIdQuery,
    cursor: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    repo=Depends(get_conversation_repo),
    tm: TaskManager = Depends(get_task_manager),
) -> PaginatedItems:
    if await repo.get_task(task_id) is None:
        if tm.get_status(task_id) is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail="Task not found"
            )
        return PaginatedItems(items=[], next_cursor=None, has_more=False)
    rows = await repo.get_subtasks(task_id, cursor=cursor, limit=limit + 1)
    has_more = len(rows) > limit
    page = rows[:limit]
    next_c = page[-1].sequence + 1 if has_more and page else None
    return PaginatedItems(
        items=[subtask_to_wire(s) for s in page],
        next_cursor=next_c,
        has_more=has_more,
    )


@tasks_router.post("/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_task(
    task_id: TaskIdQuery,
    tm: TaskManager = Depends(get_task_manager),
) -> Response:
    if not tm.cancel(task_id):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Task not running or unknown",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
