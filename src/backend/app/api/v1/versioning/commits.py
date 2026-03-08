from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import get_project_uow, ProjectUoW
from app.db.context import DbTarget
from app.db.scoped_client import scoped_client
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
    node_id: str = Query(..., description="The ID of the node"),
    start: int = Query(0, description="The start index"),
    count: int = Query(40, description="The number of commits to return"),
    project_uow: ProjectUoW = Depends(get_project_uow)
):
    """Get commit history for a project."""
    project = project_uow.project
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    target = DbTarget(db=project.db_name,
                      branch=project_uow.ctx.branch, ref=project_uow.ctx.ref)
    async with scoped_client(project_uow.client, target) as session:
        if node_id.startswith("ProjectSchema/"):
            result = await session.log(start=start, count=count)
        else:
            result = await session.get_document_history(node_id, start=start, count=count)
        return [CommitResponse.from_result(commit) for commit in result]


@router.get("/diff")
async def get_diff(

    after_commit_id: str = Query(...,
                                 description="The ID of the after commit"),
    before_commit_id: str = Query(...,
                                  description="The ID of the before commit"),

    project_uow: ProjectUoW = Depends(get_project_uow),
):
    """Get diff for a commit."""
    project = project_uow.project
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    target = DbTarget(db=project.db_name,
                      branch=project_uow.ctx.branch, ref=project_uow.ctx.ref)
    async with scoped_client(project_uow.client, target) as session:
        result = await session.diff(after=after_commit_id, before=before_commit_id)
        return result
