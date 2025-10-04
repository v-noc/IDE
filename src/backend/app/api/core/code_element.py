from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from pydantic import BaseModel

from app.core.services import (
    ContainerService,
    FileService,
    FunctionService,
    ClassService,
    CallService,
)

from app.core.repository import Repositories
from app.db.client import get_db
from arango.database import StandardDatabase
from app.core.sandbox.code_run import CodeResponse, CodeRunner
from app.api.dependencies import get_project_service
from app.core.services.project_service import ProjectService
import os

router = APIRouter()


class RunCode(BaseModel):
    code: str
    executable_path: str | None = None
    examples_path: str | None = None
    command_prefix: str | None = None
    filename: str | None = None


def _get_services(db: StandardDatabase):
    repos = Repositories(db)
    return (
        ContainerService(repos),
        FileService(repos),
        FunctionService(repos),
        ClassService(repos),
        CallService(repos),
    )


@router.get("/{code_element_id}/code")
def get_code(
    code_element_id: str,
    db: StandardDatabase = Depends(get_db),
) -> Dict[str, Any]:
    (
        container_service,
        file_service,
        function_service,
        class_service,
        call_service,
    ) = _get_services(db)
    node = container_service.get(code_element_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )

    node_type = getattr(node, "node_type", None)
    if node_type == "file":
        result = file_service.get_code(node.id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File or project not found",
            )
        return result
    elif node_type == "function":
        result = function_service.get_code(node.id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Function file or project not found",
            )
        return result
    elif node_type == "class":
        result = class_service.get_code(node.id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class file or project not found",
            )
        return result
    elif node_type == "call":
        result = call_service.get_code(node.id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call file or project not found",
            )
        return result

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported node type for code retrieval",
    )


@router.get("/{file_id}/file-code")
def get_file_code(
    file_id: str,
    db: StandardDatabase = Depends(get_db),
) -> Dict[str, Any]:
    _, file_service, _, _, _ = _get_services(db)
    result = file_service.get_code(file_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File or project not found",
        )
    return result


@router.post("/{project_id}/run-code")
def run_code(
    project_id: str,
    run_code: RunCode,
    project_service: ProjectService = Depends(get_project_service),
) -> CodeResponse:
    """Execute provided code using the project's absolute root path and
    return stdout/stderr."""
    project_node = project_service.get(project_id)
    if project_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    project_path = os.path.abspath(getattr(project_node, "path", ""))
    if not project_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project path is missing",
        )

    return CodeRunner().run_code(
        project_root_path=project_path,
        python_executable=run_code.executable_path,
        code=run_code.code,
        examples_path=run_code.examples_path,
        command_prefix=run_code.command_prefix,
        filename=run_code.filename,
    )
