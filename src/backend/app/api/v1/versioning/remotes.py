from pydantic import BaseModel
from fastapi import APIRouter, Depends

from app.db.async_terminus_client import AsyncClient
from app.db.client import get_terminus_client
from app.api.dependencies import get_project_uow, ProjectUoW
from app.db.context import DbTarget
from app.db.scoped_client import scoped_client

router = APIRouter()


class RemoteAuth(BaseModel):
    type: str = "http_basic"
    username: str | None = None
    key: str


class CloneRequest(BaseModel):
    remote_url: str
    local_db_name: str
    description: str = ""
    remote_auth: RemoteAuth | None = None


class PushRequest(BaseModel):
    remote: str = "origin"
    branch: str | None = None
    remote_branch: str | None = None
    remote_auth: RemoteAuth | None = None


class PullRequest(BaseModel):
    remote: str = "origin"
    branch: str | None = None
    remote_branch: str | None = None


class FetchRequest(BaseModel):
    remote_id: str = "origin"


@router.post("/clone")
async def clone_remote(
    request: CloneRequest,
    base: AsyncClient = Depends(get_terminus_client),
):
    client = base.clone()
    remote_auth_dict = None
    if request.remote_auth:
        remote_auth_dict = request.remote_auth.model_dump()
    await client.clonedb(
        clone_source=request.remote_url,
        newid=request.local_db_name,
        description=request.description,
        remote_auth=remote_auth_dict,
    )
    return {"ok": True, "local_db": request.local_db_name}


@router.post("/push")
async def push_remote(
    request: PushRequest,
    project_uow: ProjectUoW = Depends(get_project_uow),
):
    target = DbTarget(
        db=project_uow.project.db_name,
        branch=project_uow.ctx.branch,
    )
    async with scoped_client(project_uow.client, target) as session:
        remote_auth = request.remote_auth.model_dump() if request.remote_auth else None
        result = await session.push(
            remote=request.remote,
            remote_branch=request.remote_branch or request.branch,
            remote_auth=remote_auth,
        )
        return result


@router.post("/pull")
async def pull_remote(
    request: PullRequest,
    project_uow: ProjectUoW = Depends(get_project_uow),
):
    target = DbTarget(
        db=project_uow.project.db_name,
        branch=project_uow.ctx.branch,
    )
    async with scoped_client(project_uow.client, target) as session:
        result = await session.pull(
            remote=request.remote,
            remote_branch=request.remote_branch or request.branch,
        )
        return result


@router.post("/fetch")
async def fetch_remote(
    request: FetchRequest,
    project_uow: ProjectUoW = Depends(get_project_uow),
):
    target = DbTarget(
        db=project_uow.project.db_name,
        branch=project_uow.ctx.branch,
    )
    async with scoped_client(project_uow.client, target) as session:
        result = await session.fetch(remote_id=request.remote_id)
        return result
