"""Agent task and subtask HTTP API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.agent.conversation_store import ConversationStore
from app.agent.runner.task_manager import TaskManager
from app.api.v1.conversations.deps import (
    get_conversation_repo,
    get_conversation_store,
    get_task_manager,
)
from app.api.v1.conversations.params import ConversationIdQuery, TaskIdQuery
from app.api.v1.conversations.schemas import (
    PaginatedItems,
    subtask_to_wire,
    task_to_wire,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])

conversation_tasks_router = APIRouter(prefix="/conversations", tags=["tasks"])


@conversation_tasks_router.get("/tasks")
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


@router.get("/detail")
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


@router.get("/subtasks")
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


@router.post("/cancel", status_code=status.HTTP_204_NO_CONTENT)
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
