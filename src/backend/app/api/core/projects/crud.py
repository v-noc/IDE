from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional

from app.core.schemas.tree import ProjectTreeNode, AnyTreeNode
from app.core.parser.graph_builder import GraphBuilder
from app.core.builder.tree_builder import TreeBuilder
from app.db.client import get_db
from arango.database import StandardDatabase
from app.core.services.project_service import ProjectService
from app.api.dependencies import get_project_service
from pathlib import Path

from app.core.model.nodes import ProjectNode


class CreateProjectRequest(BaseModel):
    name: str = Field(required=True, min_length=3)
    description: str
    path: str = Field(required=True)


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)


router = APIRouter()


@router.post("/", response_model=ProjectTreeNode)
def create_project(
    project: CreateProjectRequest,
    db: StandardDatabase = Depends(get_db),
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
        graph_builder = GraphBuilder(project.path, None, db)
        graph_builder.build(project.name, project.description)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "field": "path",
                "message": str(exc),
            },
        )
    except Exception as exc:
        print(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to build project graph",
        )

    project_node = graph_builder.project_node
    children = project_service.get_children(project_node.id)

    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()

    project_tree = ProjectTreeNode(**project_node.model_dump(), children=tree)
    return project_tree


@router.get("/", response_model=list[ProjectNode])
def get_projects(
    project_service: ProjectService = Depends(get_project_service),
) -> list[AnyTreeNode]:
    projects = project_service.get_all()

    return projects


@router.get("/{project_id}/children", response_model=list[AnyTreeNode])
def get_project_children(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
) -> list[AnyTreeNode]:
    project_node = project_service.get(project_id)
    children = project_service.get_children(project_node.id)

    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()

    # project_tree = ProjectTreeNode(
    #     **project_node.model_dump(),
    #     children=tree
    # )
    return tree


@router.get("/{project_id}", response_model=ProjectTreeNode)
def get_project(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectTreeNode:
    project_node = project_service.get(project_id)
    if project_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    children = project_service.get_children(project_node.id)

    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()

    project_tree = ProjectTreeNode(**project_node.model_dump(), children=tree)
    return project_tree


@router.get("/", response_model=list[ProjectTreeNode])
def get_all_projects(
    project_service: ProjectService = Depends(get_project_service),
) -> list[AnyTreeNode]:
    projects = project_service.get_all()
    return projects


@router.delete("/{project_id}", response_model=bool)
def delete_project(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
) -> bool:
    project = project_service.get(project_id=project_id)
    if project:
        result = project_service.delete(project_id)
        if result is False:
            return False
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with {project_id} not found"
        )


@router.put("/{project_id}", response_model=ProjectNode)
def update_project(
    project_id: str,
    project: UpdateProjectRequest,
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectNode:
    project_node = project_service.get(project_id)
    if project_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    if project.name is not None:
        project_node.name = project.name
    if project.description is not None:
        project_node.description = project.description
    return project_service.update(project_node)
