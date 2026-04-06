from fastapi import APIRouter, Depends, Query, Body
from fastapi import status
from fastapi import HTTPException

from app.api.dependencies import get_container_service
from app.core.services.container_service import ContainerService
from app.core.model.properties import ThemeConfig
from pydantic import BaseModel
from typing import Optional
from app.core.model.schemas.structure_schema import INIT_FOLDER_ID


router = APIRouter()


class UpdateBasicInfoRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None


@router.put("/update-theme")
async def update_theme(
        container_id: str = Query(..., description="The ID of the container"),
        theme: ThemeConfig = Body(...),
        container_service: ContainerService = Depends(get_container_service)):
    if container_id.startswith("ProjectSchema/"):
        container_id = INIT_FOLDER_ID
    updated_node = await container_service.update_theme_config(container_id, theme)
    if updated_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Container with ID {container_id} not found or does not support themes.",
        )
    return updated_node


@router.put("/update-basic-info")
async def update_basic_info(
    container_id: str = Query(..., description="The ID of the container"),
    container_service: ContainerService = Depends(get_container_service),
    request: UpdateBasicInfoRequest = Body(...),
):

    if container_id.startswith("ProjectSchema/"):
        container_id = INIT_FOLDER_ID
    updated_node = await container_service.update_basic_info(
        container_id,
        name=request.name,
        description=request.description,
        icon=request.icon
    )
    if updated_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Container with ID {container_id} not found.",
        )
    return updated_node
