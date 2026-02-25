from fastapi import APIRouter, Depends, Query, HTTPException, status, Body
from pydantic import BaseModel, Field
from datetime import datetime
from app.db.client import get_terminus_client
from app.db.async_terminus_client import AsyncClient
from app.api.dependencies import get_db_context, get_project_service
from app.core.services.project_service import ProjectService

router = APIRouter()


class CreateBranchRequest(BaseModel):
    name: str = Field(..., description="Name of the new branch")


class BranchResponse(BaseModel):
    id: str
    name: str
    is_current: bool
    created_at: datetime
    updated_at: datetime


@router.get("/")
async def get_branches(
    project_id: str = Query(..., description="The ID of the project"),
    db: AsyncClient = Depends(get_terminus_client),
    get_db_context: dict = Depends(get_db_context),
    project_service: ProjectService = Depends(get_project_service),
):
    """Get all branches for a project."""
    project = await project_service.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    clone = db.clone()
    clone.db = project["db_name"]
    branch_name = get_db_context["branch"]
    if branch_name:
        clone.branch = branch_name
    branches = await clone.get_all_branches()
    return [BranchResponse.from_result(branch) for branch in branches]


@router.post("/")
async def create_branch(
    project_id: str = Query(..., description="The ID of the project"),
    request: CreateBranchRequest = Body(..., description="The request body"),
    db: AsyncClient = Depends(get_terminus_client),
    project_service: ProjectService = Depends(get_project_service),
):
    """Create a new branch for a project."""
    project = await project_service.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    clone = db.clone()
    clone.db = project["db_name"]
    branch_name = get_db_context["branch"]
    if branch_name:
        clone.branch = branch_name
    await clone.create_branch(request.name)
    return {"ok": True}


@router.delete("/{name}")
async def delete_branch(
    name: str,
    project_id: str = Query(..., description="The ID of the project"),
    db: AsyncClient = Depends(get_terminus_client),
    project_service: ProjectService = Depends(get_project_service),
):
    """Delete a branch for a project."""
    project = await project_service.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    clone = db.clone()
    clone.db = project["db_name"]
    branch_name = get_db_context["branch"]
    if branch_name:
        clone.branch = branch_name
    await clone.delete_branch(name)
    return {"ok": True}
