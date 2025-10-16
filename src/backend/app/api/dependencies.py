from fastapi import Depends
from app.core.repository import Repositories
from app.core.services.project_service import ProjectService
from app.db.client import get_db
from arango.database import StandardDatabase
from app.core.services.container_service import ContainerService
from app.core.services.file_service import FileService
from app.core.services.class_service import ClassService
from app.core.services.function_service import FunctionService
from app.core.services.call_service import CallService
from app.core.services.log_service import LogService


def get_project_service(
    db: StandardDatabase = Depends(get_db),
) -> ProjectService:
    repos = Repositories(db)
    return ProjectService(repos)


def get_container_service(
    db: StandardDatabase = Depends(get_db),
) -> ContainerService:
    repos = Repositories(db)
    return ContainerService(repos)


def get_file_service(
    db: StandardDatabase = Depends(get_db),
) -> FileService:
    repos = Repositories(db)
    return FileService(repos)


def get_class_service(
    db: StandardDatabase = Depends(get_db),
) -> ClassService:
    repos = Repositories(db)
    return ClassService(repos)


def get_function_service(
    db: StandardDatabase = Depends(get_db),
) -> FunctionService:
    repos = Repositories(db)
    return FunctionService(repos)


def get_call_service(
    db: StandardDatabase = Depends(get_db),
) -> CallService:
    repos = Repositories(db)
    return CallService(repos)


def get_log_service(
    db: StandardDatabase = Depends(get_db),
) -> LogService:
    repos = Repositories(db)
    return LogService(repos)
