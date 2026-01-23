from fastapi import APIRouter, Depends, HTTPException, Body, status
from typing import Dict, Any
from pydantic import BaseModel
import os

from app.core.sandbox.code_run import CodeResponse, CodeRunner
from app.db.client import get_db
from arangoasync.database import AsyncDatabase
from app.api.dependencies import (
    get_project_service,
    get_container_service,
)
from app.core.watcher.service import WatcherService, get_watcher_service
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator
from app.core.services.project_service import ProjectService
from app.core.services.container_service import ContainerService
from app.core.socket.manager import get_socket_manager


router = APIRouter()


class RunCode(BaseModel):
    code: str
    executable_path: str | None = None
    examples_path: str | None = None
    command_prefix: str | None = None
    filename: str | None = None


@router.post("/{element_id}/write-code")
async def write_code(
    element_id: str,
    code_block: str = Body(..., embed=True, alias="code"),
    container_service: ContainerService = Depends(get_container_service),
    project_service: ProjectService = Depends(get_project_service),
    watcher_service: WatcherService = Depends(get_watcher_service),
    db: AsyncDatabase = Depends(get_db),
) -> Dict[str, Any]:
    """
    Writes a block of code to the location of a given code element.
    """
    node_id = f"nodes/{element_id}"

    # Get project node and stop watcher before writing
    project_node = None
    try:
        _, project_doc = await container_service._resolve_file_and_project(node_id)
        if project_doc:
            project_id = project_doc.get("_id")
            project_node = await project_service.get(project_id)
            if project_node:
                # Stop watcher (not pause) to prevent event bubbling
                watcher_service.stop_watching(project_node.id)
    except Exception:
        # Non-fatal: failure to stop watcher should not block write
        pass

    # Write the code
    result = await container_service.write_code(node_id, code_block)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))

    # Run orchestrator manually to sync changes
    if project_node:
        try:
            orchestrator = GraphBuilderOrchestrator(
                project_node=project_node,
                db=db,
            )
            await orchestrator.resync()
        except Exception:
            # Non-fatal: failure to sync should not block write response
            pass

        # Emit code:updated socket event
        try:
            socket_manager = get_socket_manager()
            await socket_manager.emit_to_project(
                project_node.id,
                "code:updated",
                {"element_id": element_id}
            )
        except Exception:
            # Non-fatal: failure to emit socket event should not block write
            pass

        # Start watcher again after sync
        try:
            watcher_service.start_watching(project_node)
        except Exception:
            # Non-fatal: failure to start watcher should not block write
            pass

    return result


@router.get("/{element_id}/read-code")
async def get_code(
    element_id: str,
    container_service: ContainerService = Depends(get_container_service),
) -> Dict[str, Any]:
    """
    Retrieves the code for a given element.
    Accepts document key (not full _id).
    """
    node_id = f"nodes/{element_id}"
    code_details = await container_service.get_code(node_id)

    if code_details is None:
        raise HTTPException(
            status_code=404, detail="Element or code not found")

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
