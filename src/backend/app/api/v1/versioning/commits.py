from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel

from app.db.client import get_terminus_client
from app.db.async_terminus_client import AsyncClient
from app.api.dependencies import get_project_service
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
            id=result["@id"],
            message=result["message"],
            timestamp=datetime.fromtimestamp(result["timestamp"]),
            author=result["author"],
        )


@router.get("/")
async def get_commits(
    project_id: str = Query(..., description="The ID of the project"),
    node_id: str = Query(..., description="The ID of the node"),
    start: int = Query(0, description="The start index"),
    count: int = Query(10, description="The number of commits to return"),
    db: AsyncClient = Depends(get_terminus_client),
    project_service: ProjectService = Depends(get_project_service),
):
    """Get commit history for a project."""
    project = await project_service.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    clone = db.clone()
    clone.db = project["db_name"]
    result = await clone.get_document_history(node_id, start=start, count=count)
    return [CommitResponse.from_result(commit) for commit in result]
