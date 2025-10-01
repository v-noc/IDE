from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.schemas.tree import ProjectTreeNode, AnyTreeNode
from app.core.parser.graph_builder import GraphBuilder
from app.core.builder.tree_builder import TreeBuilder
from app.db.client import get_db
from arango.database import StandardDatabase
from app.core.services.project_service import ProjectService
from app.core.repository import Repositories
from app.api.dependencies import get_project_service


class CreateProjectRequest(BaseModel):
    name: str
    description: str
    path: str


router = APIRouter()


@router.post("/", response_model=ProjectTreeNode)
def create_project(
    project: CreateProjectRequest,
    db: StandardDatabase = Depends(get_db),
    project_service: ProjectService = Depends(get_project_service),
):
    graph_builder = GraphBuilder(project.path, None, db)
    graph_builder.build(project.name, project.description)

    project_node = graph_builder.project_node
    children = project_service.get_children(project_node.id)

    tree_builder = TreeBuilder(children)
    tree = tree_builder.build()

    project_tree = ProjectTreeNode(
        **project_node.model_dump(),
        children=tree
    )
    return project_tree


@router.get("/", response_model=list[ProjectTreeNode])
def get_projects(
    project_service: ProjectService = Depends(get_project_service),
) -> list[AnyTreeNode]:
    projects = project_service.get_all()
    return projects
