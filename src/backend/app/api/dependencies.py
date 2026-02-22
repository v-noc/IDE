from fastapi import Depends, Query, HTTPException
from app.core.repository import Repositories
from app.core.services.project_service import ProjectService

from app.core.services.file_service import FileService
from app.core.services.class_service import ClassService
from app.core.services.function_service import FunctionService
from app.core.services.call_service import CallService
from app.core.services.log_service import LogService
from app.core.services.group_service import GroupService
from app.core.services.document_service import DocumentService
from app.db.client import get_terminus_client
from app.db.async_terminus_client import AsyncClient
from app.core.model.nodes import ProjectNode


def get_group_service(
    db: AsyncClient = Depends(get_terminus_client),
) -> GroupService:
    repos = Repositories(db)
    return GroupService(repos)


def get_project_service(
    db: AsyncClient = Depends(get_terminus_client),
) -> ProjectService:
    repos = Repositories(db.clone())
    return ProjectService(repos)


async def get_file_service(
    db: AsyncClient = Depends(get_terminus_client),
    project_service: ProjectService = Depends(get_project_service),
    project_id: str = Query(..., description="The ID of the project to get"),
) -> FileService:
    project = await project_service.get(project_id)
    repos = Repositories(db)
    project = ProjectNode.from_raw_dict(project)
    return FileService(repos, project)


async def get_class_service(
    db: AsyncClient = Depends(get_terminus_client),
    project_service: ProjectService = Depends(get_project_service),
    project_id: str = Query(..., description="The ID of the project to get"),
) -> ClassService:
    project = await project_service.get(project_id)
    repos = Repositories(db)
    project = ProjectNode.from_raw_dict(project)
    return ClassService(repos, project)


async def get_function_service(
    project_service: ProjectService = Depends(get_project_service),
    project_id: str = Query(..., description="The ID of the project to get"),
    db: AsyncClient = Depends(get_terminus_client),
) -> FunctionService:

    project = await project_service.get(project_id)
    project = ProjectNode.from_raw_dict(project)
    repos = Repositories(db)
    return FunctionService(repos, project)


def get_call_service(
    db: AsyncClient = Depends(get_terminus_client),
) -> CallService:
    repos = Repositories(db)
    return CallService(repos)


def get_log_service(
    db: AsyncClient = Depends(get_terminus_client),
) -> LogService:
    repos = Repositories(db)
    return LogService(repos)


async def get_document_service(
    db: AsyncClient = Depends(get_terminus_client),
    project_service: ProjectService = Depends(get_project_service),
    project_id: str = Query(..., description="The ID of the project to get"),
) -> DocumentService:

    project = await project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project = ProjectNode.from_raw_dict(project)
    repos = Repositories(db)
    return DocumentService(repos, project)
