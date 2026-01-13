from fastapi import APIRouter, Depends, HTTPException, Body, status
from arangoasync.database import AsyncDatabase
from typing import Dict, Any
from pydantic import BaseModel
import os

from app.core.sandbox.code_run import CodeResponse, CodeRunner
from app.db.client import get_db
from app.core.services.project_service import ProjectService
from app.api.dependencies import (
    get_project_service,
    get_file_service,
    get_class_service,
    get_function_service,
    get_call_service,
)
from app.core.watcher.service import WatcherService, get_watcher_service
from app.core.repository import Repositories


router = APIRouter()


class RunCode(BaseModel):
    code: str
    executable_path: str | None = None
    examples_path: str | None = None
    command_prefix: str | None = None
    filename: str | None = None


def _get_services(db: AsyncDatabase):
    project_service = get_project_service(db)
    file_service = get_file_service(db)
    class_service = get_class_service(db)
    function_service = get_function_service(db)
    call_service = get_call_service(db)
    return (
        project_service,
        file_service,
        class_service,
        function_service,
        call_service,
    )


@router.post("/{element_id}/write-code")
async def write_code(
    element_id: str,
    code_block: str = Body(..., embed=True, alias="code"),
    db: AsyncDatabase = Depends(get_db),
    watcher_service: WatcherService = Depends(get_watcher_service),
) -> Dict[str, Any]:
    """
    Writes a block of code to the location of a given code element.
    """
    project_service, file_service, _, _, _ = _get_services(db)

    # Ensure the project's watcher is running for this element
    try:
        node_repo = Repositories(db).nodes
        raw_node = await node_repo.get_raw_by_key(element_id)
        if raw_node:
            current_id = raw_node.get("_id")
            # Walk up to find the project ancestor
            parent = await node_repo.get_parent_project(current_id)
            if parent:
                project_node = await project_service.get(parent.id)
                # TODO: do a syncer
                if project_node:
                    watcher_service.start_watching(project_node)
    except Exception:
        # Non-fatal: failure to start watcher should not block write
        pass
    result = await file_service.write_code_by_id(element_id, code_block)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.get("/{element_id}/code")
async def get_code(
    element_id: str,
    db: AsyncDatabase = Depends(get_db),
) -> Dict[str, Any]:
    """
    Retrieves the code for a given element by first determining its type.
    Accepts document key (not full _id).
    """
    node_repo = Repositories(db).nodes
    raw_node = await node_repo.get_raw_by_key(element_id)

    if not raw_node:
        raise HTTPException(status_code=404, detail="Element not found")

    node_type = raw_node.get("node_type")
    node_id = raw_node.get("_id")  # full id like nodes/123

    if not node_type or not node_id:
        raise HTTPException(status_code=500, detail="Node data is corrupted")

    (
        _,
        file_service,
        class_service,
        function_service,
        call_service,
    ) = _get_services(db)

    if node_type == "file":
        code_details = await file_service.get_code(node_id)
    elif node_type == "function":
        code_details = await function_service.get_code(node_id)
    elif node_type == "class":
        code_details = await class_service.get_code(node_id)
    elif node_type == "call":
        code_details = await call_service.get_code(node_id)
    else:
        raise HTTPException(
            status_code=400, detail=f"Unsupported node type: {node_type}")

    if code_details is None:
        raise HTTPException(
            status_code=404, detail="Code not found for element")

    return code_details


@router.post("/{project_id}/run-code")
async def run_code(
    project_id: str,
    run_code: RunCode,
    project_service: ProjectService = Depends(get_project_service),
) -> CodeResponse:
    """Execute provided code using the project's absolute root path and
    return stdout/stderr."""
    project_node = await project_service.get(project_id)
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

    return await CodeRunner().run_code(
        project_root_path=project_path,
        python_executable=run_code.executable_path,
        code=run_code.code,
        examples_path=run_code.examples_path,
        command_prefix=run_code.command_prefix,
        filename=run_code.filename,
    )
