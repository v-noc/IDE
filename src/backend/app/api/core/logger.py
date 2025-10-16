from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import get_log_service
from app.core.schemas.log_tree import LogTreeNode
from app.core.services.log_service import LogService


router = APIRouter()


class GetLogTreeRequest(BaseModel):
    pass


@router.get("/{function_id}/log-tree")
def get_function_log(
    function_id: str,
    service: LogService = Depends(get_log_service),
) -> List[LogTreeNode]:
    return service.get_function_log(function_id)


@router.get("/{call_id}/call-log")
def get_call_log(
    call_id: str,
    service: LogService = Depends(get_log_service),
) -> List[LogTreeNode]:
    return service.get_call_log(call_id)


@router.get("/{log_id}/containment-tree")
def get_log_containment_tree(
    log_id: str,
    service: LogService = Depends(get_log_service),
) -> List[LogTreeNode]:
    return service.get_log_containment_tree(log_id)


@router.get("/{node_id}/tree")
def get_unified_log_tree(
    node_id: str,
    service: LogService = Depends(get_log_service),
) -> List[LogTreeNode]:
    return service.get_unified_log_tree(node_id)
