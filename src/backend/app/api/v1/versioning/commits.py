from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel

from app.db.client import get_terminus_client
from app.db.async_terminus_client import AsyncClient
from app.api.dependencies import get_project_service, get_db_context
from app.core.services.project_service import ProjectService

router = APIRouter()


class CommitResponse(BaseModel):
    id: str
    message: str
    timestamp: datetime
    author: str

    @staticmethod
    def from_result(result: dict) -> "CommitResponse":

        return CommitResponse(
            id=result["identifier"],
            message=result["message"],
            timestamp=result["timestamp"],
            author=result["author"],

        )


@router.get("/")
async def get_commits(
    project_id: str = Query(..., description="The ID of the project"),
    node_id: str = Query(..., description="The ID of the node"),
    start: int = Query(0, description="The start index"),
    count: int = Query(10, description="The number of commits to return"),
    db: AsyncClient = Depends(get_terminus_client),
    get_db_context: dict = Depends(get_db_context),
    project_service: ProjectService = Depends(get_project_service),
):
    """Get commit history for a project."""
    project = await project_service.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    clone = db.clone()
    clone.db = project["db_name"]
    branch_name = get_db_context["branch"]
    if branch_name:
        clone.branch = branch_name
    if node_id.startswith("ProjectSchema/"):
        result = await clone.log(start=start, count=count)
    else:
        result = await clone.get_document_history(node_id, start=start, count=count)
    return [CommitResponse.from_result(commit) for commit in result]


@router.get("/diff")
async def get_diff(
    project_id: str = Query(..., description="The ID of the project"),
    after_commit_id: str = Query(...,
                                 description="The ID of the after commit"),
    before_commit_id: str = Query(...,
                                  description="The ID of the before commit"),
    get_db_context: dict = Depends(get_db_context),
    db: AsyncClient = Depends(get_terminus_client),
    project_service: ProjectService = Depends(get_project_service),
):
    """Get diff for a commit."""
    project = await project_service.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    clone = db.clone()
    clone.db = project["db_name"]
    branch_name = get_db_context["branch"]

    if branch_name:
        clone.branch = branch_name
    result = await clone.diff_version(after_version=after_commit_id, before_version=before_commit_id)
    return result
