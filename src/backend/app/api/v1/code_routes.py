from fastapi import APIRouter, Depends, HTTPException, Body, Query, status
from fastapi_cache.decorator import cache
from pydantic import BaseModel
from typing import Any, Dict, Optional

from app.api.dependencies import (
    ProjectUoW,
    get_code_element_service,
    get_project_node,
    get_project_uow,
)
from app.core.model.nodes import ProjectNode
from app.core.watcher.service import WatcherService, get_watcher_service
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator

from app.core.socket.manager import get_socket_manager
from app.core.services import CodeElementService
from app.core.builder.tree_builder import TreeBuilder
from app.core.schemas.tree import AnyTreeNode
from app.core.cache_setup import DEFAULT_TTL


router = APIRouter()


class CodeDescendantsResponse(BaseModel):
    """Code subtree under ``parent_id``, same nested shape as project tree (TreeBuilder)."""

    children: list[dict[str, Any]]


class CodeLineageResponse(BaseModel):
    """Path from project root to ``target_id`` and nested spine built with TreeBuilder."""

    path_ids: list[str]
    tree: list[dict[str, Any]]


def _parse_child_type_query(raw: Optional[str]) -> list[str]:
    if not raw or not raw.strip():
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


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
@cache(expire=DEFAULT_TTL)
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


@router.get("/descendants", response_model=CodeDescendantsResponse)
@cache(expire=DEFAULT_TTL)
async def get_code_descendants(
    parent_id: str = Query(
        ...,
        description="Anchor document id (e.g. FileSchema/…, ClassSchema/…)",
    ),
    depth_start: Optional[int] = Query(
        None,
        ge=1,
        description="Minimum path hops from parent (WOQL path times lower bound)",
    ),
    depth_max: Optional[int] = Query(
        None,
        ge=1,
        description="Maximum path hops from parent (WOQL path times upper bound)",
    ),
    child_types: Optional[str] = Query(
        None,
        description="Comma-separated kinds: function,class,call,code_element_group,call_group",
    ),
    project_node: ProjectNode = Depends(get_project_node),
    code_element_service: CodeElementService = Depends(get_code_element_service),
) -> CodeDescendantsResponse:
    _ = project_node  # resolves project DB context (project_id query param)

    if (
        depth_start is not None
        and depth_max is not None
        and depth_start > depth_max
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="depth_start must be <= depth_max",
        )

    kinds = _parse_child_type_query(child_types)
    compare_to = code_element_service.uow.has_compare_to()
    base_nodes, base_target_lookup = await code_element_service.get_code_descendants(
        parent_id,
        kinds,
        depth_start=depth_start,
        depth_max=depth_max,
        compare_to=False,
    )
    compare_nodes = None
    merged_target_lookup = dict(base_target_lookup)
    if compare_to:
        compare_nodes, compare_target_lookup = await code_element_service.get_code_descendants(
            parent_id,
            kinds,
            depth_start=depth_start,
            depth_max=depth_max,
            compare_to=True,
        )
        merged_target_lookup.update(compare_target_lookup)
    else:
        compare_nodes = None

    tree_builder = TreeBuilder(
        base_nodes, compare_nodes, target_lookup=merged_target_lookup
    )
    trees: list[AnyTreeNode] = tree_builder.build()
    serialized = [n.model_dump(mode="json") for n in trees]
    return CodeDescendantsResponse(children=serialized)


@router.get("/lineage", response_model=CodeLineageResponse)
@cache(expire=DEFAULT_TTL)
async def get_code_lineage(
    target_id: str = Query(
        ...,
        description="Document id to resolve from root (e.g. FunctionSchema/…, ClassSchema/…)",
    ),
    project_node: ProjectNode = Depends(get_project_node),
    code_element_service: CodeElementService = Depends(get_code_element_service),
) -> CodeLineageResponse:
    _ = project_node
    compare_to = code_element_service.uow.has_compare_to()
    data = await code_element_service.get_target_lineage_tree(
        target_id, compare_to=compare_to
    )
    return CodeLineageResponse(**data)
