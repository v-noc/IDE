from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_project_uow
from app.db.context import ProjectUoW
from app.walkthrough.schemas import Estimate
from app.walkthrough.service import WalkthroughService

router = APIRouter()


def get_walkthrough_service(
    uow: ProjectUoW = Depends(get_project_uow),
) -> WalkthroughService:
    return WalkthroughService(uow)


@router.get("/estimate", response_model=Estimate)
async def get_estimate(
    node_id: str = Query(..., description="Canvas node id to tour from"),
    depth: int = Query(1, ge=0, le=3, description="How many levels below the start node"),
    service: WalkthroughService = Depends(get_walkthrough_service),
) -> Estimate:
    try:
        result = await service.estimate(node_id, depth)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return Estimate(
        node_count=result.node_count,
        step_estimate=result.step_estimate,
        llm_call_estimate=result.llm_call_estimate,
        over_cap=result.over_cap,
    )
