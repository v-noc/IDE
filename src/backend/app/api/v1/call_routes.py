from fastapi import APIRouter
from pydantic import BaseModel, Field
from fastapi import Depends
from app.core.services.call_service import CallService
from app.api.dependencies import (
    get_call_service,
    get_function_service,
    get_container_service,
)
from app.core.services.function_service import FunctionService
from app.core.services.container_service import ContainerService
from fastapi import HTTPException, status
from app.core.model.properties import CodePosition

router = APIRouter()


class AddCallRequest(BaseModel):
    callee_target_id: str = Field(
        ..., description="The target ID of the callee function"
    )
    name: str = Field(..., description="The name of the call")
    description: str = Field(..., description="The description of the call")


@router.post("/{caller_node_id}/add-call")
async def add_call(
    caller_node_id: str,
    add_call: AddCallRequest,
    call_service: CallService = Depends(get_call_service),
    function_service: FunctionService = Depends(get_function_service),
    container_service: ContainerService = Depends(get_container_service),
):

    callee_function_node = await function_service.get(add_call.callee_target_id)
    if not callee_function_node:
        raise HTTPException(status_code=404, detail="Function node not found")

    parent_node = await container_service.get(caller_node_id)
    if not parent_node:
        raise HTTPException(
            status_code=404, detail="Parent function node not found")

    if parent_node.node_type not in ["function", "class", "file", "call"]:
        raise HTTPException(
            status_code=400,
            detail=(
                "Parent node is not a function, class, file, or call"
            ),
        )

    # Get parent's current_version for version inheritance
    # Use parent's version, defaulting to 0 if not set
    parent_version = getattr(parent_node, 'current_version', None)
    if parent_version is None:
        parent_version = 0

    call = await call_service.create(
        name=add_call.name,
        qname=f"{callee_function_node.qname}L{0}C{0}",
        description=add_call.description,
        position=CodePosition(
            line_no=0,
            col_offset=0,
            end_line_no=0,
            end_col_offset=0,
        ),
        target_id=callee_function_node.id,
        manually_created=True,
        current_version=parent_version,
    )

    await container_service.add_child_to_container(
        parent_node.id,
        call.id,
        f"{parent_node.node_type}_to_call",
        version=parent_version,
    )

    # Clone callee's internal call graph (calls and groups) under the new call
    await container_service.clone_callee_call_graph(
        callee_function_node.id,
        call.id,
    )

    return call


@router.delete("/{call_key}/remove-call", status_code=status.HTTP_204_NO_CONTENT)
async def remove_call(
    call_key: str,
    call_service: CallService = Depends(get_call_service),
):
    call = await call_service.get(call_key)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    await call_service.delete(call_key)
