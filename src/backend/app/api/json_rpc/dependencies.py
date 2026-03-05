from typing import Optional
from fastapi import Depends, Body

from app.db.client import get_terminus_client
from app.db.context import RequestDbContext, ProjectUoW
from app.core.model.nodes import ProjectNode
from app.core.services.log_service import LogService

from app.api.dependencies import get_project_service


def get_jsonrpc_request_db_context() -> RequestDbContext:
    """JSON-RPC uses default branch/ref since params come from body."""
    return RequestDbContext(branch="main", ref=None)


def get_jsonrpc_project_id(
    project_id: str = Body(..., embed=True, alias="project_id"),
) -> str:
    return project_id


async def get_jsonrpc_project_node(
    project_id: str = Depends(get_jsonrpc_project_id),
    project_service=Depends(get_project_service),
) -> Optional[ProjectNode]:
    try:
        project = await project_service.get(project_id)
        return ProjectNode.from_raw_dict(project) if project else None
    except Exception as e:
        print("Error getting project", e)
        return None


async def get_jsonrpc_project_uow(
    base=Depends(get_terminus_client),
    project: Optional[ProjectNode] = Depends(get_jsonrpc_project_node),
    ctx: RequestDbContext = Depends(get_jsonrpc_request_db_context),
):
    """Async generator dependency. FastAPI enters it and passes the yielded ProjectUoW."""
    try:
        yield ProjectUoW(base, project, ctx)
    finally:
        pass


async def get_project(
    project_node: Optional[ProjectNode] = Depends(get_jsonrpc_project_node),
):
    return project_node


def get_log_service(
    uow: ProjectUoW = Depends(get_jsonrpc_project_uow),
) -> LogService:
    return LogService(uow)
