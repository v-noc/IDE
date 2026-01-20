from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from typing import List
from fastapi import Depends
from app.core.services.group_service import GroupService
from app.api.dependencies import get_group_service

router = APIRouter()


class CreateGroupRequest(BaseModel):
    name: str = Field(..., description="The name of the group")
    description: str = Field(..., description="The description of the group")
    children_ids: List[str] = Field(..., description="The IDs of the children")


class AddChildRequest(BaseModel):
    child_id: str = Field(..., description="The ID of the child")


class RemoveChildRequest(AddChildRequest):
    pass


@router.post("/{parent_node_id}/create-group")
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


@router.delete("/{group_id}/delete-group", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: str,
    group_service: GroupService = Depends(get_group_service),
):
    await group_service.delete(group_id, remove_children=True)


@router.post("/{group_id}/add-child")
async def add_child(
    group_id: str,
    add_child: AddChildRequest,
    group_service: GroupService = Depends(get_group_service),
):
    return await group_service.add_child_to_group(group_id, add_child.child_id)


@router.delete("/{group_id}/remove-child", status_code=status.HTTP_204_NO_CONTENT)
async def remove_child(
    group_id: str,
    remove_child: RemoveChildRequest,
    group_service: GroupService = Depends(get_group_service),
):
    await group_service.remove_child_from_group(group_id, remove_child.child_id)
