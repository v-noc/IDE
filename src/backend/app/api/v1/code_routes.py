from fastapi import APIRouter, Depends, HTTPException, Body, Query, status
from typing import Dict, Any, Optional
from pydantic import BaseModel
import os

from app.core.sandbox.code_run import CodeResponse, CodeRunner

from app.api.dependencies import (
    ProjectUoW,
    get_code_element_service,
    get_project_uow,
)
from app.core.watcher.service import WatcherService, get_watcher_service
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator

from app.core.socket.manager import get_socket_manager
from app.core.services import CodeElementService


router = APIRouter()


class RunCode(BaseModel):
    code: str
    executable_path: str | None = None
    examples_path: str | None = None
    command_prefix: str | None = None
    filename: str | None = None


@router.post("/write-code")
async def write_code(
    node_id: str = Query(...,
                         description="The ID of the node to write code to"),

    code_block: str = Body(..., embed=True, alias="code"),
    code_element_service: CodeElementService = Depends(
        get_code_element_service),
    watcher_service: WatcherService = Depends(get_watcher_service),
    project_uow: ProjectUoW = Depends(get_project_uow),
) -> Dict[str, Any]:
    """
    Writes a block of code to the location of a given code element.
    Accepts code element ID.
    """

    # Get project node and stop watcher before writing (to prevent event bubbling)
    project_node = project_uow.project
    if project_node:
        try:
            watcher_service.stop_watching(project_node.id)
        except Exception:
            pass

    # Route to appropriate service by node_id prefix (same as get_code)

    result = await code_element_service.write_code(node_id, code_block)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))

    # Run orchestrator, emit socket, restart watcher
    if project_node:
        try:
            orchestrator = GraphBuilderOrchestrator(
                project_node=project_node,
                uow=project_uow,
            )
            await orchestrator.resync()
        except Exception:
            pass

        # Emit code:updated socket event
        try:
            socket_manager = get_socket_manager()
            await socket_manager.emit_to_project(
                project_node.id,
                "code:updated",
                {"element_id": node_id},
            )
        except Exception:
            pass

        # Start watcher again after sync
        try:
            watcher_service.start_watching(project_node)
        except Exception:
            pass

    return result


@router.get("/read-code/")
async def get_code(
    node_id: str = Query(..., description="The ID of the element to get"),
    code_element_service: CodeElementService = Depends(
        get_code_element_service),
) -> Dict[str, Any]:
    """
    Retrieves the code for a given element.
    Accepts document key (not full _id).
    """

    code_details = await code_element_service.get_code(node_id)

    if code_element_service.uow.has_compare_to():

        compare_to_code_details = await code_element_service.get_code(node_id, compare_to=True)

        if compare_to_code_details is not None:
            if code_details is not None:
                code_details["compare_to"] = compare_to_code_details
            else:
                code_details = {"compare_to": compare_to_code_details,
                                **compare_to_code_details, "code": ""}

    if code_details is None:
        raise HTTPException(
            status_code=404, detail="Element or code not found")

    return code_details


@router.post("/run-code")
async def run_code(

    run_code: RunCode,
    project_uow: ProjectUoW = Depends(get_project_uow),
) -> CodeResponse:
    """Execute provided code using the project's absolute root path and
    return stdout/stderr."""
    project_node = project_uow.project
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
