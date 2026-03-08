from fastapi import APIRouter, Depends,  HTTPException, status, Body
from pydantic import BaseModel, Field
from datetime import datetime
from app.api.dependencies import get_project_uow, ProjectUoW
from app.db.scoped_client import scoped_client
from app.db.context import DbTarget


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
    project_uow: ProjectUoW = Depends(get_project_uow),
):
    """Get all branches for a project."""
    project = project_uow.project
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    target = DbTarget(db=project.db_name,
                      branch=project_uow.ctx.branch, ref=project_uow.ctx.ref)
    async with scoped_client(project_uow.client, target) as session:
        branches = await session.get_all_branches()
        return [BranchResponse.from_result(branch) for branch in branches]


@router.post("/")
async def create_branch(
    request: CreateBranchRequest = Body(..., description="The request body"),
    project_uow: ProjectUoW = Depends(get_project_uow),
):
    """Create a new branch for a project."""
    project = project_uow.project
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    target = DbTarget(db=project.db_name,
                      branch=project_uow.ctx.branch, ref=project_uow.ctx.ref)
    async with scoped_client(project_uow.client, target) as session:
        await session.create_branch(request.name)
        return {"ok": True}


@router.delete("/{name}")
async def delete_branch(
    name: str,
    project_uow: ProjectUoW = Depends(get_project_uow),
):
    """Delete a branch for a project."""
    project = project_uow.project
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    target = DbTarget(db=project.db_name,
                      branch=project_uow.ctx.branch, ref=project_uow.ctx.ref)
    async with scoped_client(project_uow.client, target) as session:
        await session.delete_branch(name)
        return {"ok": True}
