from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from typing import List, Optional
from fastapi import Depends
from app.core.services.group_service import GroupService
from app.api.dependencies import get_group_service

router = APIRouter()


class CreateGroupRequest(BaseModel):
    name: str = Field(..., description="The name of the group")
    description: str = Field(..., description="The description of the group")
    children_ids: List[str] = Field(..., description="The IDs of the children")


class UpdateGroupRequest(BaseModel):
    name: Optional[str] = Field(None, description="The name of the group")
    description: Optional[str] = Field(None, description="The description of the group")


class AddChildRequest(BaseModel):
    child_id: str = Field(..., description="The ID of the child")


@router.post("/{parent_node_id}")
async def create_group(
    parent_node_id: str,
    create_group: CreateGroupRequest,
    group_service: GroupService = Depends(get_group_service),
):
    return await group_service.create(
        create_group.name,
        create_group.description,
        parent_node_id,
        children_ids=create_group.children_ids,
    )


@router.patch("/{group_id}")
async def update_group(
    group_id: str,
    update_data: UpdateGroupRequest,
    group_service: GroupService = Depends(get_group_service),
):
    return await group_service.update_basic_info(
        group_id,
        name=update_data.name,
        description=update_data.description,
        icon=None,
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: str,
    group_service: GroupService = Depends(get_group_service),
):
    await group_service.delete(group_id, remove_children=True)


@router.post("/{group_id}/children")
async def add_child(
    group_id: str,
    add_child: AddChildRequest,
    group_service: GroupService = Depends(get_group_service),
):
    return await group_service.add_child_to_group(group_id, add_child.child_id)


@router.delete("/{group_id}/children/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_child(
    group_id: str,
    child_id: str,
    group_service: GroupService = Depends(get_group_service),
):
    await group_service.remove_child_from_group(group_id, child_id)
