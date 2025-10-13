from fastapi import APIRouter, Depends, HTTPException, Body
from arango.database import StandardDatabase
from typing import Dict, Any

from app.db.client import get_db
from app.core.services.file_service import FileService
from app.core.services.class_service import ClassService
from app.core.services.function_service import FunctionService
from app.core.services.project_service import ProjectService
from app.core.services.call_service import CallService
from app.api.dependencies import get_project_service, get_file_service, get_class_service, get_function_service, get_call_service
from app.core.repository import Repositories


router = APIRouter()


def _get_services(db: StandardDatabase):
    project_service = get_project_service(db)
    file_service = get_file_service(db)
    class_service = get_class_service(db)
    function_service = get_function_service(db)
    call_service = get_call_service(db)
    return project_service, file_service, class_service, function_service, call_service


@router.post("/{element_id}/write-code")
def write_code(
    element_id: str,
    code_block: str = Body(..., embed=True, alias="code"),
    db: StandardDatabase = Depends(get_db),
) -> Dict[str, Any]:
    """
    Writes a block of code to the location of a given code element.
    """
    _, file_service, _, _, _ = _get_services(db)
    result = file_service.write_code_by_id(element_id, code_block)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.get("/{element_id}/code")
def get_code(
    element_id: str,
    db: StandardDatabase = Depends(get_db),
) -> Dict[str, Any]:
    """
    Retrieves the code for a given element by first determining its type.
    Accepts document key (not full _id).
    """
    node_repo = Repositories(db).nodes
    raw_node = node_repo.get_raw_by_key(element_id)

    if not raw_node:
        raise HTTPException(status_code=404, detail="Element not found")

    node_type = raw_node.get("node_type")
    node_id = raw_node.get("_id")  # full id like nodes/123

    if not node_type or not node_id:
        raise HTTPException(status_code=500, detail="Node data is corrupted")

    _, file_service, class_service, function_service, call_service = _get_services(
        db)

    if node_type == "file":
        code_details = file_service.get_code(node_id)
    elif node_type == "function":
        code_details = function_service.get_code(node_id)
    elif node_type == "class":
        code_details = class_service.get_code(node_id)
    elif node_type == "call":
        code_details = call_service.get_code(node_id)
    else:
        raise HTTPException(
            status_code=400, detail=f"Unsupported node type: {node_type}")

    if code_details is None:
        raise HTTPException(
            status_code=404, detail="Code not found for element")

    return code_details


@router.get("/{file_id}/file-code")
def get_file_code(
    file_id: str,
    db: StandardDatabase = Depends(get_db),
) -> Dict[str, Any]:
    """
    Deprecated alias: retrieve code for a file node by key.
    """
    file_service = get_file_service(db)
    file_node = file_service.get(file_id)

    if not file_node or getattr(file_node, "node_type", None) != "file":
        raise HTTPException(status_code=404, detail="File element not found")

    code_details = file_service.get_code(file_node.id)
    if code_details is None:
        raise HTTPException(status_code=404, detail="Code not found for file")

    return code_details
