from fastapi import Depends
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


def get_file_service(
    db: AsyncClient = Depends(get_terminus_client),
) -> FileService:
    repos = Repositories(db)
    return FileService(repos)


def get_class_service(
    db: AsyncClient = Depends(get_terminus_client),
) -> ClassService:
    repos = Repositories(db)
    return ClassService(repos)


def get_function_service(
    db: AsyncClient = Depends(get_terminus_client),
) -> FunctionService:
    repos = Repositories(db)
    return FunctionService(repos)


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


def get_document_service(
    db: AsyncClient = Depends(get_terminus_client),
) -> DocumentService:
    repos = Repositories(db)
    return DocumentService(repos)
