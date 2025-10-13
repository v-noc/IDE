from fastapi import Depends, Body
from arango.database import StandardDatabase

from app.db.client import get_db
from app.core.repository import Repositories
from app.core.services.project_service import ProjectService
from app.core.services.file_service import FileService
from app.core.services.class_service import ClassService
from app.core.services.function_service import FunctionService
from app.core.services.call_service import CallService


def get_services(db: StandardDatabase = Depends(get_db)):
    repos = Repositories(db)
    return (
        ProjectService(repos),
        FileService(repos),
        ClassService(repos),
        FunctionService(repos),
        CallService(repos),
    )


def get_project(
    project_id: str = Body(..., embed=True, alias="project_id"),
    services=Depends(get_services),
):
    project_service, *_ = services
    project = project_service.get(project_id)
    if project is None:
        from .error import ProjectNotFoundError

        raise ProjectNotFoundError
    return project


def get_element_services(services=Depends(get_services)):
    _, file_service, class_service, function_service, call_service = services
    return file_service, class_service, function_service, call_service
