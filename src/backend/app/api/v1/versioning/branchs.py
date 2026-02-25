from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.db.client import get_terminus_client
from app.db.async_terminus_client import AsyncClient
from app.api.dependencies import get_project_service
from app.core.services.project_service import ProjectService

router = APIRouter()


@router.get("/")
async def get_branches(
    project_id: str = Query(..., description="The ID of the project"),
    db: AsyncClient = Depends(get_terminus_client),
    project_service: ProjectService = Depends(get_project_service),
):
    """Get all branches for a project."""
    project = await project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    clone = db.clone()
    clone.db = project["db_name"]
    return await clone.get_all_branches()


@router.post("/")
async def create_branch(
    project_id: str = Query(..., description="The ID of the project"),
    name: str = Query(..., description="Name of the new branch"),
    db: AsyncClient = Depends(get_terminus_client),
    project_service: ProjectService = Depends(get_project_service),
):
    """Create a new branch for a project."""
    project = await project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    clone = db.clone()
    clone.db = project["db_name"]
    await clone.create_branch(name)
    return {"ok": True}
