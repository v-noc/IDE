from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional

from app.core.schemas.tree import ProjectTreeNode, AnyTreeNode
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator
from app.core.builder.tree_builder import TreeBuilder
from app.db.client import get_db
from arangoasync.database import AsyncDatabase
from app.core.repository import Repositories
from app.core.services.project_service import ProjectService
from app.api.dependencies import get_project_service
from pathlib import Path
from app.core.watcher.service import WatcherService, get_watcher_service
from loguru import logger

from app.core.model.nodes import ProjectNode


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
    db: AsyncDatabase = Depends(get_db),
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
        project_node = ProjectNode(
            name=project.name,
            description=project.description or "",
            qname=project.name.lower().replace(" ", "_"),
            path=project.path,
        )
        project_node = await project_service.create_node(project_node)

        orchestrator = GraphBuilderOrchestrator(
            project_node=project_node,
            db=db,

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

    children = await project_service.get_children(project_node.id)

    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()

    project_tree = ProjectTreeNode(**project_node.model_dump(), children=tree)
    return project_tree


@router.get("/", response_model=list[ProjectNode])
async def get_projects(
    project_service: ProjectService = Depends(get_project_service),
) -> list[AnyTreeNode]:
    projects = await project_service.get_all()

    return projects


@router.get("/{project_id}/children", response_model=list[AnyTreeNode])
async def get_project_children(
    project_id: str,
    exclude_groups: bool = False,
    project_service: ProjectService = Depends(get_project_service),
) -> list[AnyTreeNode]:
    project_node = await project_service.get(project_id)
    children = await project_service.get_children(
        project_node.id, exclude_groups=exclude_groups)

    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()

    return tree


@router.get("/{project_id}", response_model=ProjectTreeNode)
async def get_project(
    project_id: str,
    exclude_groups: bool = False,
    project_service: ProjectService = Depends(get_project_service),
    watcher_service: WatcherService = Depends(get_watcher_service),
) -> ProjectTreeNode:
    project_node = await project_service.get(project_id)
    if project_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    watcher_service.start_watching(project_node)

    children = await project_service.get_children(
        project_node.id, exclude_groups=exclude_groups)

    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()

    project_tree = ProjectTreeNode(**project_node.model_dump(), children=tree)
    return project_tree


@router.get("/", response_model=list[ProjectTreeNode])
async def get_all_projects(
    project_service: ProjectService = Depends(get_project_service),
) -> list[AnyTreeNode]:
    projects = await project_service.get_all()
    return projects


@router.delete("/{project_id}", response_model=bool)
async def delete_project(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
) -> bool:
    project = await project_service.get(project_id=project_id)
    if project:
        result = await project_service.delete(project)
        if result is False:
            return False

        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with {project_id} not found"
        )


@router.put("/{project_id}", response_model=ProjectNode)
async def update_project(
    project_id: str,
    project: UpdateProjectRequest,
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectNode:
    project_node = await project_service.get(project_id)
    if project_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    if project.name is not None:
        project_node.name = project.name
    if project.description is not None:
        project_node.description = project.description
    return await project_service.update(project_node)
