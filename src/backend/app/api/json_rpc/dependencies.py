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
    try:
        project_service, *_ = services
        project = project_service.get(project_id)

        return project
    except Exception as e:
        print("Error getting project", e)
        return None


def get_function_services(services=Depends(get_services)):
    _, _, _, function_service, _ = services
    return function_service


def get_function(
    function_id: str = Body(..., embed=True, alias="function_id"),
    services=Depends(get_function_services),
):
    func_node = None
    try:
        function_service = services

        func_node = function_service.get(function_id)

    except Exception as e:
        print("Error getting function", e)
    finally:
        return func_node


def get_parent_function(
    parent_function_id: str = Body(..., embed=True,
                                   alias="parent_function_id"),
    services=Depends(get_function_services),
):
    parent_func_node = None
    try:
        function_service = services

        parent_func_node = function_service.get(parent_function_id)

    except Exception as e:
        print("Error getting function", e)
    finally:
        return parent_func_node
