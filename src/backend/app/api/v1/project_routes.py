from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, model_validator
from terminusdb_client.errors import InterfaceError

from app.api.dependencies import (
    ProjectUoW,
    get_project_node,
    get_project_service,
    get_project_service_with_uow,
)
from app.api.schemas.terminus_remote import RemoteConfig
from app.core.builder.tree_builder import TreeBuilder
from app.core.model.nodes import ProjectNode
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator
from app.core.schemas.tree import AnyTreeNode, ProjectTreeNode
from app.core.services.project_service import ProjectService
from app.core.watcher.service import WatcherService, get_watcher_service
from app.db.async_terminus_client import AsyncClient
from app.db.client import get_terminus_client
from app.db.context import RequestDbContext
from app.db.errors import DatabaseError
from app.core.model.schemas import StructureGroupSchema
from loguru import logger


class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=3)
    description: Optional[str] = Field(default=None)
    path: str = Field(...)
    remote: Optional[RemoteConfig] = None
    remote_mode: Literal["none", "create_remote", "clone"] = Field(
        default="none",
        description="none: local only. create_remote: bootstrap on remote URL then clonedb locally. clone: full clone URL only.",
    )

    @model_validator(mode="after")
    def _remote_matches_mode(self):
        if self.remote is None:
            if self.remote_mode != "none":
                raise ValueError("remote is required when remote_mode is not none")
        elif self.remote_mode == "none":
            raise ValueError("remote_mode cannot be none when remote is set")
        return self


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)


router = APIRouter()


def _exclude_types_for_groups(exclude_groups: bool) -> list[str]:
    return [StructureGroupSchema.__name__] if exclude_groups else []


@router.post("/", response_model=ProjectTreeNode)
async def create_project(
    project: CreateProjectRequest,
    db: AsyncClient = Depends(get_terminus_client),
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectTreeNode:
    """Create a project graph from a local path.

    Optional ``remote`` + ``remote_mode`` integrate Terminus remotes (see OpenAPI field docs).
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

    desc = project.description or ""

    try:
        if project.remote_mode == "none":
            project_node = await project_service.create(
                name=project.name,
                description=desc,
                path=project.path,
            )
        elif project.remote_mode == "create_remote":
            rc = project.remote
            assert rc is not None
            project_node = await project_service.create_with_remote_bootstrap(
                local_client=db,
                name=project.name,
                description=desc,
                path=project.path,
                remote=rc,
            )
        else:
            rc = project.remote
            assert rc is not None
            project_node = await project_service.create_from_remote_clone(
                local_client=db,
                name=project.name,
                description=desc,
                path=project.path,
                remote=rc,
            )

        uow = ProjectUoW(
            db,
            project_node,
            RequestDbContext(branch="main", ref=None),
        )
        orchestrator = GraphBuilderOrchestrator(
            project_node=project_node,
            uow=uow,
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
    except InterfaceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": str(exc)},
        )
    except DatabaseError as exc:
        logger.exception("Terminus database error during project create")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": str(exc)},
        )
    except Exception as exc:
        logger.exception(f"Failed to build project graph: {exc}")
        raise

    project_service.uow = uow
    children, version = await project_service.get_children(include_commit_id=True)

    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()

    return ProjectTreeNode(**project_node.model_dump(), children=tree)


@router.get("/", response_model=ProjectTreeNode)
async def get_project(
    project_node: ProjectNode = Depends(get_project_node),
    exclude_groups: bool = False,
    project_service: ProjectService = Depends(get_project_service_with_uow),
    watcher_service: WatcherService = Depends(get_watcher_service),
) -> ProjectTreeNode:

    watcher_service.start_watching(project_node)

    exclude_types = _exclude_types_for_groups(exclude_groups)
    children, version = await project_service.get_children(
        exclude_types=exclude_types,
        include_commit_id=True,
    )

    compare_to_children = None
    if project_service.uow.has_compare_to():
        compare_to_children, compare_to_version = await project_service.get_children(
            exclude_types=exclude_types,
            compare_to=True,
            include_commit_id=True,
        )

    tree_builder = TreeBuilder(children, compare_to_children)
    tree = tree_builder.build()

    project_tree = ProjectTreeNode(
        **project_node.model_dump(), children=tree, version=version)
    return project_tree


@router.get("/structure", response_model=ProjectTreeNode)
async def get_project_structure(
    project_node: ProjectNode = Depends(get_project_node),
    exclude_groups: bool = Query(
        False, description="Omit structure-group documents from the tree"
    ),
    project_service: ProjectService = Depends(get_project_service_with_uow),
    watcher_service: WatcherService = Depends(get_watcher_service),
) -> ProjectTreeNode:
    """Load folder/file/(optional) structure-group shell only — no code elements."""
    watcher_service.start_watching(project_node)

    exclude_types = _exclude_types_for_groups(exclude_groups)
    structure_nodes, version = await project_service.get_structure(
        exclude_types=exclude_types,
        include_commit_id=True,
    )

    compare_to_structure = None
    if project_service.uow.has_compare_to():
        compare_to_structure, _ = await project_service.get_structure(
            exclude_types=exclude_types,
            include_commit_id=True,
            compare_to=True,
        )

    tree_builder = TreeBuilder(structure_nodes, compare_to_structure)
    tree = tree_builder.build()

    return ProjectTreeNode(
        **project_node.model_dump(),
        children=tree,
        version=version,
    )


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
