from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple
from fastapi import Depends
from app.core.services.group_service import GroupService, GroupType
from app.api.dependencies import get_group_service

router = APIRouter()


class ChildRef(BaseModel):
    id: str = Field(..., description="The ID of the child")
    type: str = Field(..., description="The type of the child (e.g. folder, file, structure_group)")


class CreateGroupRequest(BaseModel):
    name: str = Field(..., description="The name of the group")
    description: str = Field(..., description="The description of the group")
    children: List[ChildRef] = Field(default_factory=list, description="The children to add to the group")


class UpdateGroupRequest(BaseModel):
    name: Optional[str] = Field(None, description="The name of the group")
    description: Optional[str] = Field(None, description="The description of the group")


class AddChildRequest(BaseModel):
    child_id: str = Field(..., description="The ID of the child")
    item_type: str = Field(..., description="The type of the child (e.g. folder, file, structure_group)")


def _parse_group_type(value: str) -> GroupType:
    try:
        return GroupType(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid group_type. Must be one of: {', '.join(gt.value for gt in GroupType)}",
        )


@router.post("")
async def create_group(
    create_group: CreateGroupRequest,
    group_service: GroupService = Depends(get_group_service),
    parent_node_id: str = Query(..., description="The ID of the parent node to create the group under"),
    group_type: str = Query(..., description="Group type: structure_group, code_element_group, or call_group"),
    x_vnoc_branch: Optional[str] = Header(None, alias="X-Vnoc-Branch"),
):
    gt = _parse_group_type(group_type)
    children: List[Tuple[str, str]] = [(c.id, c.type) for c in create_group.children]
    result = await group_service.create(
        create_group.name,
        create_group.description,
        parent_node_id,
        children=children,
        group_type=gt,
        branch_name=x_vnoc_branch,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create group",
        )
    return result


@router.patch("/{group_id}")
async def update_group(
    group_id: str,
    update_data: UpdateGroupRequest,
    group_service: GroupService = Depends(get_group_service),
    group_type: str = Query(..., description="Group type: structure_group, code_element_group, or call_group"),
    x_vnoc_branch: Optional[str] = Header(None, alias="X-Vnoc-Branch"),
):
    gt = _parse_group_type(group_type)
    return await group_service.update_basic_info(
        group_id,
        group_type=gt,
        name=update_data.name,
        description=update_data.description,
        icon=None,
        branch_name=x_vnoc_branch,
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: str,
    group_service: GroupService = Depends(get_group_service),
    group_type: str = Query(..., description="Group type: structure_group, code_element_group, or call_group"),
    x_vnoc_branch: Optional[str] = Header(None, alias="X-Vnoc-Branch"),
):
    gt = _parse_group_type(group_type)
    await group_service.delete(group_id, group_type=gt, branch_name=x_vnoc_branch)


@router.post("/{group_id}/children")
async def add_child(
    group_id: str,
    add_child_req: AddChildRequest,
    group_service: GroupService = Depends(get_group_service),
    group_type: str = Query(..., description="Group type: structure_group, code_element_group, or call_group"),
    x_vnoc_branch: Optional[str] = Header(None, alias="X-Vnoc-Branch"),
):
    gt = _parse_group_type(group_type)
    return await group_service.add_child_to_group(
        group_id,
        add_child_req.child_id,
        add_child_req.item_type,
        group_type=gt,
        branch_name=x_vnoc_branch,
    )


@router.delete("/{group_id}/children/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_child(
    group_id: str,
    child_id: str,
    group_service: GroupService = Depends(get_group_service),
    group_type: str = Query(..., description="Group type: structure_group, code_element_group, or call_group"),
    item_type: str = Query(..., description="The type of the child being removed"),
    new_parent_id: str = Query(..., description="The ID of the parent to move the child to"),
    x_vnoc_branch: Optional[str] = Header(None, alias="X-Vnoc-Branch"),
):
    gt = _parse_group_type(group_type)
    await group_service.remove_child_from_group(
        group_id,
        child_id,
        item_type=item_type,
        new_parent_id=new_parent_id,
        group_type=gt,
        branch_name=x_vnoc_branch,
    )
