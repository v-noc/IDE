from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.dependencies import get_test_service
from app.core.services.test_service import TestService

router = APIRouter()


class CreateTestConfigRequest(BaseModel):
    enabled: bool = Field(default=True)
    test_root: str = Field(..., min_length=1)
    test_args: str = Field(default="")


class UpdateTestConfigRequest(BaseModel):
    enabled: Optional[bool] = None
    test_root: Optional[str] = Field(default=None, min_length=1)
    test_args: Optional[str] = None


class TestConfigResponse(BaseModel):
    id: str
    enabled: bool
    test_root: str
    test_args: str


class RunTestsRequest(BaseModel):
    node_id: Optional[str] = Field(
        default=None,
        description=(
            "Node id of a test case. "
            "Will be treated as test target path/node."
        ),
    )
    owner_id: Optional[str] = Field(
        default=None,
        description=(
            "Owner function/class/file id. "
            "Runs all related test cases."
        ),
    )


class RunResult(BaseModel):
    exit_code: int
    test_cases: int
    test_links: int
    persisted: bool


class RunTestsResponse(BaseModel):
    mode: str
    run: Optional[RunResult] = None
    runs: list[RunResult] = Field(default_factory=list)
    total_runs: int = 0
    total_test_cases: int = 0
    total_test_links: int = 0


@router.get("/config", response_model=TestConfigResponse)
async def get_test_config(
    test_service: TestService = Depends(get_test_service),
) -> TestConfigResponse:
    config = await test_service.get_test_config()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test config not found",
        )
    return TestConfigResponse(
        id=config.get("@id", ""),
        enabled=config.get("enabled", False),
        test_root=config.get("test_root", ""),
        test_args=config.get("test_args", ""),
    )


@router.post("/config", response_model=TestConfigResponse)
async def create_test_config(
    request: CreateTestConfigRequest,
    test_service: TestService = Depends(get_test_service),
) -> TestConfigResponse:
    ok = await test_service.create_or_update_config(
        enabled=request.enabled,
        test_root=request.test_root,
        test_args=request.test_args,
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create test config",
        )
    config = await test_service.get_test_config()
    return TestConfigResponse(
        id=config.get("@id", ""),
        enabled=config.get("enabled", False),
        test_root=config.get("test_root", ""),
        test_args=config.get("test_args", ""),
    )


@router.put("/config", response_model=TestConfigResponse)
async def update_test_config(
    request: UpdateTestConfigRequest,
    test_service: TestService = Depends(get_test_service),
) -> TestConfigResponse:
    if (
        request.enabled is None
        and request.test_root is None
        and request.test_args is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field is required for update",
        )

    config = await test_service.update_test_config(
        enabled=request.enabled,
        test_root=request.test_root,
        test_args=request.test_args,
    )
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test config not found",
        )

    return TestConfigResponse(
        id=config.get("@id", ""),
        enabled=config.get("enabled", False),
        test_root=config.get("test_root", ""),
        test_args=config.get("test_args", ""),
    )


@router.delete("/config", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_config(
    test_service: TestService = Depends(get_test_service),
):
    ok = await test_service.delete_test_config()
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test config not found or delete failed",
        )
    return None


@router.post("/run", response_model=RunTestsResponse)
async def run_tests(
    request: RunTestsRequest,
    test_service: TestService = Depends(get_test_service),
) -> RunTestsResponse:
    has_node_id = bool(request.node_id)
    has_owner_id = bool(request.owner_id)
    if has_node_id == has_owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide exactly one of node_id or owner_id",
        )

    if request.node_id:
        run_result = await test_service.run_tests(request.node_id)
        run = RunResult(**run_result)
        return RunTestsResponse(
            mode="node_id",
            run=run,
            runs=[run],
            total_runs=1,
            total_test_cases=run.test_cases,
            total_test_links=run.test_links,
        )

    owner_result = await test_service.run_tests_for_owner(request.owner_id)
    runs = [RunResult(**item) for item in owner_result.get("runs", [])]
    return RunTestsResponse(
        mode="owner_id",
        runs=runs,
        total_runs=owner_result.get("total_runs", 0),
        total_test_cases=owner_result.get("total_test_cases", 0),
        total_test_links=owner_result.get("total_test_links", 0),
    )
