from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.dependencies import get_play_ground_service
from app.core.sandbox.code_run import CodeResponse
from app.core.services.play_ground_service import PlayGroundService

router = APIRouter()


class PlayGroundResponse(BaseModel):
    id: str
    name: str
    description: str
    relative_path: str
    code: str
    executable_path: Optional[str] = None
    filename: Optional[str] = None
    owner_function: Optional[str] = None
    owner_class: Optional[str] = None
    owner_file: Optional[str] = None
    owner_folder: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CreatePlayGroundRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(default="")
    relative_path: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    executable_path: Optional[str] = None
    filename: Optional[str] = None
    owner_function: Optional[str] = None
    owner_class: Optional[str] = None
    owner_file: Optional[str] = None
    owner_folder: Optional[str] = None


class UpdatePlayGroundRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    relative_path: Optional[str] = Field(default=None, min_length=1)
    code: Optional[str] = Field(default=None, min_length=1)
    executable_path: Optional[str] = None
    filename: Optional[str] = None


class RunPlayGroundRequest(BaseModel):
    playground_id: str = Field(..., min_length=1)


def _owner_count(request: CreatePlayGroundRequest) -> int:
    return len(
        [
            owner
            for owner in [
                request.owner_function,
                request.owner_class,
                request.owner_file,
                request.owner_folder,
            ]
            if owner
        ]
    )


def _to_response(raw: dict) -> PlayGroundResponse:
    return PlayGroundResponse(
        id=raw.get("@id", ""),
        name=raw.get("name", ""),
        description=raw.get("description", ""),
        relative_path=raw.get("relative_path", ""),
        code=raw.get("code", ""),
        executable_path=raw.get("executable_path"),
        filename=raw.get("filename"),
        owner_function=raw.get("owner_function"),
        owner_class=raw.get("owner_class"),
        owner_file=raw.get("owner_file"),
        owner_folder=raw.get("owner_folder"),
        created_at=raw.get("created_at"),
        updated_at=raw.get("updated_at"),
    )


@router.post(
    "/",
    response_model=PlayGroundResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_playground(
    request: CreatePlayGroundRequest,
    play_ground_service: PlayGroundService = Depends(get_play_ground_service),
) -> PlayGroundResponse:
    owner_count = _owner_count(request)
    if owner_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "One owner is required: owner_function, owner_class, "
                "owner_file, or owner_folder"
            ),
        )
    if owner_count > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Playground can only belong to one owner",
        )

    try:
        created = await play_ground_service.create_playground(
            name=request.name,
            description=request.description,
            relative_path=request.relative_path,
            code=request.code,
            executable_path=request.executable_path,
            filename=request.filename,
            owner_function=request.owner_function,
            owner_class=request.owner_class,
            owner_file=request.owner_file,
            owner_folder=request.owner_folder,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if not created:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create playground",
        )
    return _to_response(created)


@router.get("/{playground_id}", response_model=PlayGroundResponse)
async def get_playground(
    playground_id: str,
    play_ground_service: PlayGroundService = Depends(get_play_ground_service),
) -> PlayGroundResponse:
    playground = await play_ground_service.get_playground_by_id(playground_id)
    if not playground:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playground not found",
        )
    return _to_response(playground)


@router.put("/{playground_id}", response_model=PlayGroundResponse)
async def update_playground(
    playground_id: str,
    request: UpdatePlayGroundRequest,
    play_ground_service: PlayGroundService = Depends(get_play_ground_service),
) -> PlayGroundResponse:
    if (
        request.name is None
        and request.description is None
        and request.relative_path is None
        and request.code is None
        and request.executable_path is None
        and request.filename is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field is required for update",
        )

    updated = await play_ground_service.update_playground(
        playground_id=playground_id,
        name=request.name,
        description=request.description,
        relative_path=request.relative_path,
        code=request.code,
        executable_path=request.executable_path,
        filename=request.filename,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playground not found",
        )
    return _to_response(updated)


@router.delete("/{playground_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playground(
    playground_id: str,
    play_ground_service: PlayGroundService = Depends(get_play_ground_service),
):
    deleted = await play_ground_service.delete_playground(playground_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playground not found or delete failed",
        )
    return None


@router.get(
    "/owners/function/{owner_function_id}",
    response_model=list[PlayGroundResponse],
)
async def get_playgrounds_by_owner_function_id(
    owner_function_id: str,
    play_ground_service: PlayGroundService = Depends(get_play_ground_service),
) -> list[PlayGroundResponse]:
    items = await play_ground_service.get_by_owner_function_id(
        owner_function_id
    )
    return [_to_response(item) for item in items]


@router.get(
    "/owners/class/{owner_class_id}",
    response_model=list[PlayGroundResponse],
)
async def get_playgrounds_by_owner_class_id(
    owner_class_id: str,
    play_ground_service: PlayGroundService = Depends(get_play_ground_service),
) -> list[PlayGroundResponse]:
    items = await play_ground_service.get_by_owner_class_id(owner_class_id)
    return [_to_response(item) for item in items]


@router.get(
    "/owners/file/{owner_file_id}",
    response_model=list[PlayGroundResponse],
)
async def get_playgrounds_by_owner_file_id(
    owner_file_id: str,
    play_ground_service: PlayGroundService = Depends(get_play_ground_service),
) -> list[PlayGroundResponse]:
    items = await play_ground_service.get_by_owner_file_id(owner_file_id)
    return [_to_response(item) for item in items]


@router.get(
    "/owners/folder/{owner_folder_id}",
    response_model=list[PlayGroundResponse],
)
async def get_playgrounds_by_owner_folder_id(
    owner_folder_id: str,
    play_ground_service: PlayGroundService = Depends(get_play_ground_service),
) -> list[PlayGroundResponse]:
    items = await play_ground_service.get_by_owner_folder_id(owner_folder_id)
    return [_to_response(item) for item in items]


@router.post("/run-code", response_model=CodeResponse)
async def run_playground_code(
    request: RunPlayGroundRequest,
    play_ground_service: PlayGroundService = Depends(get_play_ground_service),
) -> CodeResponse:
    try:
        return await play_ground_service.run_code(request.playground_id)
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_400_BAD_REQUEST
        if message == "Playground not found":
            status_code = status.HTTP_404_NOT_FOUND
        elif message == "Project not found":
            status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=status_code, detail=message) from exc
