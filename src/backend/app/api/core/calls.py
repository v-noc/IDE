from fastapi import APIRouter
from pydantic import BaseModel, Field
from arango.database import StandardDatabase
from fastapi import Depends
from app.db.client import get_db
from app.core.services.call_service import CallService
from app.api.dependencies import get_call_service, get_function_service, get_container_service
from app.core.services.function_service import FunctionService
from app.core.services.container_service import ContainerService
from fastapi import HTTPException
from app.core.model.properties import CodePosition

router = APIRouter()


class AddCallRequest(BaseModel):
    callee_target_id: str = Field(...,
                                  description="The target ID of the callee function")
    name: str = Field(..., description="The name of the call")
    description: str = Field(..., description="The description of the call")


@router.post("/{caller_node_id}/add-call")
def add_call(
    caller_node_id: str,
    add_call: AddCallRequest,
    call_service: CallService = Depends(get_call_service),
    function_service: FunctionService = Depends(get_function_service),
    container_service: ContainerService = Depends(get_container_service),
):

    callee_function_node = function_service.get(add_call.callee_target_id)
    if not callee_function_node:
        raise HTTPException(status_code=404, detail="Function node not found")

    parent_node = container_service.get(caller_node_id)
    if not parent_node:
        raise HTTPException(
            status_code=404, detail="Parent function node not found")

    if parent_node.node_type not in ["function", "class", "file", "call"]:
        raise HTTPException(
            status_code=400, detail="Parent node is not a function, class, file, or call")

    call = call_service.create(
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
    )

    container_service.add_child_to_container(
        parent_node.id, call.id, f"{parent_node.node_type}_to_call")

    return call


@router.delete("/{call_key}/remove-call")
def remove_call(
    call_key: str,
    call_service: CallService = Depends(get_call_service),
):
    call = call_service.get(call_key)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    call_service.delete(call_key)
    return {"message": "Call removed successfully"}
