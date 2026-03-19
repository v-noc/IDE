from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional

from app.core.schemas.tree import ProjectTreeNode, AnyTreeNode
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator
from app.core.builder.tree_builder import TreeBuilder
from app.db.client import get_terminus_client

from app.core.services.project_service import ProjectService
from app.api.dependencies import ProjectUoW, get_project_service, get_project_service_with_uow, get_project_node
from pathlib import Path
from app.core.watcher.service import WatcherService, get_watcher_service
from loguru import logger
import time
from app.core.model.nodes import ProjectNode
from app.db.async_terminus_client import AsyncClient
from app.db.context import RequestDbContext


class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=3)
    description: Optional[str] = Field(default=None)
    path: str = Field(...)


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)


router = APIRouter()


@router.post("/", response_model=ProjectTreeNode)
async def create_project(
    project: CreateProjectRequest,
    db: AsyncClient = Depends(get_terminus_client),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectTreeNode:
    """Create a project graph from a local path.

    Returns a `ProjectTreeNode` built from the analyzed source code if
    successful.
    Raises 400 when the provided path does not exist.
    """
    project_root = Path(project.path)
    if not project_root.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "field": "path",
                "message": f"Project path {project.path} does not exist",
            },
        )

    try:
        project_node = await project_service.create(
            name=project.name,
            description=project.description or "",
            path=project.path,
        )
        uow = ProjectUoW(db, project_node, RequestDbContext(
            branch="main", ref=None))

        orchestrator = GraphBuilderOrchestrator(
            project_node=project_node,
            uow=uow
        )
        await orchestrator.resync()

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "field": "path",
                "message": str(exc),
            },
        )
    except Exception as exc:
        # Let the global exception handler return 500, but preserve traceback
        logger.exception(f"Failed to build project graph: {exc}")
        raise

    project_service.uow = uow
    children, _ = await project_service.get_children()

    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()

    project_tree = ProjectTreeNode(**project_node.model_dump(), children=tree)

    return project_tree


@router.get("/", response_model=ProjectTreeNode)
async def get_project(
    project_node: ProjectNode = Depends(get_project_node),
    exclude_groups: bool = False,
    project_service: ProjectService = Depends(get_project_service_with_uow),
    watcher_service: WatcherService = Depends(get_watcher_service),
) -> ProjectTreeNode:

    watcher_service.start_watching(project_node)

    children, version = await project_service.get_children(include_commit_id=True)

    compare_to_children = None
    if project_service.uow.has_compare_to():
        compare_to_children, compare_to_version = await project_service.get_children(compare_to=True, include_commit_id=True)
        print(f"compare_to_version: {compare_to_version}")

    tree_builder = TreeBuilder(children, compare_to_children)
    tree = tree_builder.build()

    project_tree = ProjectTreeNode(
        **project_node.model_dump(), children=tree, version=version)
    return project_tree


@router.get("/all", response_model=list[ProjectNode])
async def get_projects(
    project_service: ProjectService = Depends(get_project_service),
) -> list[AnyTreeNode]:

    projects = await project_service.get_all()

    return projects


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str = Query(...,
                            description="The ID of the project to delete"),

    project_service: ProjectService = Depends(get_project_service),
):

    project = await project_service.get(project_id=project_id)

    if project:
        result = await project_service.delete(project_id)

        if result is False:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete project {project_id}"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with {project_id} not found"
        )


@router.put("/", response_model=ProjectNode)
async def update_project(
    project_id: str = Query(...,
                            description="The ID of the project to update"),
    project: UpdateProjectRequest = Body(...),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectNode:
    project_node = await project_service.get(project_id)
    if project_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    project_node = ProjectNode.from_raw_dict(project_node)
    if project.name is not None:
        project_node.name = project.name
    if project.description is not None:
        project_node.description = project.description
    return await project_service.update(project_node)
