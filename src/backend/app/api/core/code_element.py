from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from app.core.services.container_service import ContainerService
from app.core.services.file_service import FileService
from app.core.services.function_service import FunctionService
from app.core.services.class_service import ClassService
from app.core.services.call_service import CallService
from app.core.repository import Repositories
from app.db.client import get_db
from arango.database import StandardDatabase

router = APIRouter()


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
