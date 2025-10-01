from fastapi import APIRouter, Depends
from fastapi import status
from fastapi import HTTPException

from app.api.dependencies import get_container_service
from app.core.services.container_service import ContainerService
from app.core.model.properties import ThemeConfig
from app.core.model import AllNodes
from pydantic import BaseModel, Field
from typing import Optional


router = APIRouter()


class UpdateBasicInfoRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, min_length=1)
    icon: Optional[str] = Field(None)


@router.put("/{container_id}/update-theme", response_model=AllNodes)
def update_theme(container_id: str, theme: ThemeConfig, container_service: ContainerService = Depends(get_container_service)):
    updated_node = container_service.update_theme_config(container_id, theme)
    if updated_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Container with ID {container_id} not found or does not support themes.",
        )
    return updated_node


@router.put("/{container_id}/update-basic-info", response_model=AllNodes)
def update_basic_info(
    container_id: str,
    request: UpdateBasicInfoRequest,
    container_service: ContainerService = Depends(get_container_service)
):
    updated_node = container_service.update_basic_info(
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
