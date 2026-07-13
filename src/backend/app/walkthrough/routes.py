from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.agent.llm.providers import models_catalog
from app.api.dependencies import get_code_element_service, get_project_uow
from app.core.services.code_element_service import CodeElementService
from app.db.context import ProjectUoW
from app.walkthrough.schemas import Estimate, RunRequest
from app.walkthrough.service import WalkthroughService

router = APIRouter()


def get_walkthrough_service(
    uow: ProjectUoW = Depends(get_project_uow),
) -> WalkthroughService:
    return WalkthroughService(uow)


@router.get("/models")
async def list_models() -> dict:
    """Active model + provider catalog for the future picker. Never returns keys."""
    return models_catalog()


@router.get("/estimate", response_model=Estimate)
async def get_estimate(
    node_id: str = Query(..., description="Canvas node id to tour from"),
    depth: int = Query(1, ge=0, le=5, description="How many levels below the start node"),
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


@router.post("/run")
async def run_walkthrough(
    body: RunRequest,
    service: WalkthroughService = Depends(get_walkthrough_service),
    code_service: CodeElementService = Depends(get_code_element_service),
) -> StreamingResponse:
    try:
        return service.run(body, code_service)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
