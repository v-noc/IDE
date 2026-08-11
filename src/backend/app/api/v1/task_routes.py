from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.dependencies import get_task_service
from app.core.services.task_service import TaskService, TaskServiceError

router = APIRouter()


class CreateTaskRequest(BaseModel):
    title: str = Field(..., min_length=1)
    task_type: Literal["epic", "task", "bug", "improvement"] = "task"
    priority: Literal["none", "low", "medium", "high", "urgent"] = "none"
    description: str = ""
    labels: list[str] = Field(default_factory=list)
    status: Optional[str] = None
    anchors: list[dict[str, str]] = Field(default_factory=list)
    subtask_of: Optional[str] = None


class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    task_type: Optional[Literal["epic", "task", "bug", "improvement"]] = None
    priority: Optional[Literal["none", "low", "medium", "high", "urgent"]] = None
    labels: Optional[list[str]] = None


class MoveTaskRequest(BaseModel):
    status: str
    rank: str


class SubtaskRequest(BaseModel):
    child_id: Optional[str] = None
    title: Optional[str] = None
    task_type: Literal["epic", "task", "bug", "improvement"] = "task"
    priority: Literal["none", "low", "medium", "high", "urgent"] = "none"
    description: str = ""
    anchors: list[dict[str, str]] = Field(default_factory=list)


class BlockedByRequest(BaseModel):
    blocker_id: str


class AnchorRequest(BaseModel):
    node_id: str


class MoveAnchorRequest(BaseModel):
    from_node_id: str
    to_node_id: str


class NoteRequest(BaseModel):
    text: str = Field(..., min_length=1)


class UpdateBoardRequest(BaseModel):
    columns: list[dict[str, Any]]


def _handle_service_error(exc: TaskServiceError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/board")
async def get_board(
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.get_board_payload()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_task(
    request: CreateTaskRequest,
    task_service: TaskService = Depends(get_task_service),
):
    try:
        return await task_service.create_task(
            title=request.title,
            task_type=request.task_type,
            priority=request.priority,
            description=request.description,
            labels=set(request.labels),
            status=request.status,
            anchors=request.anchors,
            subtask_of=request.subtask_of,
        )
    except TaskServiceError as exc:
        _handle_service_error(exc)


@router.patch("/")
async def update_task(
    task_id: str = Query(..., description="Task id (e.g. TaskSchema/{uuid})"),
    request: UpdateTaskRequest = ...,
    task_service: TaskService = Depends(get_task_service),
):
    try:
        return await task_service.update_task(
            task_id,
            title=request.title,
            description=request.description,
            task_type=request.task_type,
            priority=request.priority,
            labels=set(request.labels) if request.labels is not None else None,
        )
    except TaskServiceError as exc:
        _handle_service_error(exc)


@router.post("/move")
async def move_task(
    task_id: str = Query(..., description="Task id (e.g. TaskSchema/{uuid})"),
    request: MoveTaskRequest = ...,
    task_service: TaskService = Depends(get_task_service),
):
    try:
        return await task_service.move_task(
            task_id,
            status=request.status,
            rank=request.rank,
        )
    except TaskServiceError as exc:
        _handle_service_error(exc)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str = Query(..., description="Task id (e.g. TaskSchema/{uuid})"),
    task_service: TaskService = Depends(get_task_service),
):
    try:
        await task_service.delete_task(task_id)
    except TaskServiceError as exc:
        _handle_service_error(exc)
    return None


@router.post("/subtasks")
async def add_subtask(
    task_id: str = Query(..., description="Parent task id"),
    request: SubtaskRequest = ...,
    task_service: TaskService = Depends(get_task_service),
):
    try:
        inline = None
        if request.child_id is None:
            if not request.title:
                raise HTTPException(
                    status_code=422,
                    detail="title required for inline subtask create",
                )
            inline = {
                "title": request.title,
                "task_type": request.task_type,
                "priority": request.priority,
                "description": request.description,
                "anchors": request.anchors,
            }
        return await task_service.add_subtask(
            task_id,
            child_id=request.child_id,
            inline=inline,
        )
    except TaskServiceError as exc:
        _handle_service_error(exc)


@router.delete("/subtasks", status_code=status.HTTP_204_NO_CONTENT)
async def remove_subtask(
    task_id: str = Query(..., description="Parent task id"),
    child_id: str = Query(..., description="Child task id"),
    task_service: TaskService = Depends(get_task_service),
):
    try:
        await task_service.remove_subtask(task_id, child_id)
    except TaskServiceError as exc:
        _handle_service_error(exc)
    return None


@router.post("/blocked-by")
async def add_blocked_by(
    task_id: str = Query(..., description="Task id"),
    request: BlockedByRequest = ...,
    task_service: TaskService = Depends(get_task_service),
):
    try:
        return await task_service.add_blocked_by(task_id, request.blocker_id)
    except TaskServiceError as exc:
        _handle_service_error(exc)


@router.delete("/blocked-by", status_code=status.HTTP_204_NO_CONTENT)
async def remove_blocked_by(
    task_id: str = Query(..., description="Task id"),
    blocker_id: str = Query(..., description="Blocker task id"),
    task_service: TaskService = Depends(get_task_service),
):
    try:
        await task_service.remove_blocked_by(task_id, blocker_id)
    except TaskServiceError as exc:
        _handle_service_error(exc)
    return None


@router.post("/anchors")
async def add_anchor(
    task_id: str = Query(..., description="Task id"),
    request: AnchorRequest = ...,
    task_service: TaskService = Depends(get_task_service),
):
    try:
        return await task_service.add_anchor(task_id, request.node_id)
    except TaskServiceError as exc:
        _handle_service_error(exc)


@router.delete("/anchors", status_code=status.HTTP_204_NO_CONTENT)
async def remove_anchor(
    task_id: str = Query(..., description="Task id"),
    node_id: str = Query(..., description="Anchor node id"),
    task_service: TaskService = Depends(get_task_service),
):
    try:
        await task_service.remove_anchor(task_id, node_id)
    except TaskServiceError as exc:
        _handle_service_error(exc)
    return None


@router.post("/anchors/move")
async def move_anchor(
    task_id: str = Query(..., description="Task id"),
    request: MoveAnchorRequest = ...,
    task_service: TaskService = Depends(get_task_service),
):
    try:
        return await task_service.move_anchor(
            task_id,
            from_node_id=request.from_node_id,
            to_node_id=request.to_node_id,
        )
    except TaskServiceError as exc:
        _handle_service_error(exc)


@router.get("/anchor-summary")
async def anchor_summary(
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.anchor_summary()


@router.get("/re-anchor-candidates")
async def re_anchor_candidates(
    qname: str = Query(...),
    kind: Optional[str] = Query(None),
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.re_anchor_candidates(qname, kind)


@router.get("/suggest-dependencies")
async def suggest_dependencies(
    node_id: str = Query(...),
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.suggest_dependencies(node_id)


@router.post("/notes")
async def add_note(
    task_id: str = Query(..., description="Task id"),
    request: NoteRequest = ...,
    task_service: TaskService = Depends(get_task_service),
):
    try:
        return await task_service.add_note(task_id, request.text)
    except TaskServiceError as exc:
        _handle_service_error(exc)


@router.patch("/board-columns")
async def update_board(
    request: UpdateBoardRequest,
    task_service: TaskService = Depends(get_task_service),
):
    try:
        return await task_service.update_board(request.columns)
    except TaskServiceError as exc:
        _handle_service_error(exc)
