from typing import List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.dependencies import get_log_service
from app.core.schemas.log_tree import LogTreeNode
from app.core.services.log_service import LogService


router = APIRouter()


class GetLogTreeRequest(BaseModel):
    pass


@router.get("/log-tree")
async def get_log_tree(
    function_id: str = Query(...,
                             description="The ID of the function to get the log tree for"),
    service: LogService = Depends(get_log_service),
) -> List[LogTreeNode]:
    return await service.get_function_log(function_id)
