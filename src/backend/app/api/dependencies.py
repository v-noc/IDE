from typing import Optional
from fastapi import Depends, Header, Query, HTTPException
from app.core.repository import Repositories
from app.core.services.project_service import ProjectService


from app.core.services.call_service import CallService
from app.core.services.log_service import LogService
from app.core.services.group_service import GroupService
from app.core.services.document_service import DocumentService
from app.db.client import get_terminus_client
from app.db.async_terminus_client import AsyncClient
from app.core.model.nodes import ProjectNode
from app.db.context import RequestDbContext, ProjectUoW

# app/api/dependencies/project_uow.py
from contextlib import asynccontextmanager
from fastapi import Depends

from app.core.model.nodes import ProjectNode
from app.core.repository import Repositories


def get_project_service(
    db: AsyncClient = Depends(get_terminus_client),
) -> ProjectService:
    repos = Repositories(db.clone())
    return ProjectService(repos)


async def get_request_db_context(
    branch: str = Header("main", alias="X-Vnoc-Branch"),
    ref: Optional[str] = Query(
        None, description="Specific commit/ref to query"),
) -> RequestDbContext:
    return RequestDbContext(branch=branch, ref=ref)


async def get_project_node(
    project_id: str = Query(..., description="The ID of the project"),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectNode:
    project = await project_service.get(project_id)
    return ProjectNode.from_raw_dict(project)


@asynccontextmanager
async def get_project_uow(
    base: AsyncClient = Depends(get_terminus_client),
    project: ProjectNode = Depends(get_project_node),
    ctx: RequestDbContext = Depends(get_request_db_context),
):
    try:
        yield ProjectUoW(base, project, ctx)
    finally:
        # clone shares base session; typically no close here
        pass


def get_group_service(
    uow: ProjectUoW = Depends(get_project_uow)
) -> GroupService:
    return GroupService(uow)


def get_call_service(
    uow: ProjectUoW = Depends(get_project_uow)
) -> CallService:

    return CallService(uow)


def get_log_service(
    uow: ProjectUoW = Depends(get_project_uow)
) -> LogService:

    return LogService(uow)


def get_document_service(uow: ProjectUoW = Depends(get_project_uow)) -> DocumentService:
    return DocumentService(uow)
