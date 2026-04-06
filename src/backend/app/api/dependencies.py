from typing import Optional
from fastapi import Depends, Header, HTTPException, Query, status
from app.core.services.project_service import ProjectService
from app.core.services.code_element_service import CodeElementService

from app.core.services.call_service import CallService
from app.core.services.log_service import LogService
from app.core.services.group_service import GroupService
from app.core.services.document_service import DocumentService
from app.core.services.test_service import TestService
from app.core.services.play_ground_service import PlayGroundService
from app.core.services.container_service import ContainerService
from app.db.client import get_terminus_client
from app.db.async_terminus_client import AsyncClient
from app.core.model.nodes import ProjectNode
from app.db.context import RequestDbContext, ProjectUoW


def get_project_service(
    db: AsyncClient = Depends(get_terminus_client),
) -> ProjectService:
    pow = ProjectUoW(db.clone(), None, RequestDbContext())
    return ProjectService(pow)


async def get_request_db_context(
    branch: str = Header("main", alias="X-Vnoc-Branch"),
    ref: Optional[str] = Query(
        None, description="Specific commit/ref to query"),
    compare_to: Optional[str] = Query(
        None, description="Commit/ref to compare against"),
) -> RequestDbContext:
    return RequestDbContext(branch=branch, ref=ref, compare_to=compare_to)


async def get_project_node(
    project_id: str = Query(..., description="The ID of the project"),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectNode:

    project = await project_service.get(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )

    try:
        return ProjectNode.from_raw_dict(project)
    except (TypeError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid project payload for id: {project_id}",
        ) from exc


async def get_project_uow(
    base: AsyncClient = Depends(get_terminus_client),
    project: ProjectNode = Depends(get_project_node),
    ctx: RequestDbContext = Depends(get_request_db_context),
):
    """Yield project UoW for request context."""
    try:
        yield ProjectUoW(base, project, ctx)
    finally:
        pass


def get_project_service_with_uow(
    uow: ProjectUoW = Depends(get_project_uow),
) -> ProjectService:
    return ProjectService(uow)


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


async def get_code_element_service(
    uow: ProjectUoW = Depends(get_project_uow)
) -> CodeElementService:
    return CodeElementService(uow)


def get_document_service(
    uow: ProjectUoW = Depends(get_project_uow),
) -> DocumentService:
    return DocumentService(uow)


def get_test_service(
    uow: ProjectUoW = Depends(get_project_uow),
) -> TestService:
    return TestService(uow)


def get_play_ground_service(
    uow: ProjectUoW = Depends(get_project_uow),
) -> PlayGroundService:
    return PlayGroundService(uow)


def get_container_service(
    uow: ProjectUoW = Depends(get_project_uow),
) -> ContainerService:
    return ContainerService(uow)
