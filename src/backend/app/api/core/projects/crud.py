from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from app.core.manager import CodeGraphManager

from pydantic import BaseModel

from app.core.parser.project_scanner import ProjectScanner
from app.api.core.folder.virtual_folders import VirtualFolderResponse
from app.models.properties import ThemeConfig


# Pydantic models for request and response
class ProjectCreate(BaseModel):
    name: str
    path: str


class ProjectUpdate(BaseModel):
    name: str
    path: str


class ProjectResponse(BaseModel):
    key: str
    name: str
    path: str


class ProjectTreeResponse(BaseModel):
    key: str
    name: str
    icon: Optional[str]
    description: Optional[str]
    node_type: str
    qname: str
    properties: dict
    theme: Optional[ThemeConfig] = None
    children: List["ProjectTreeResponse"]


def map_tree_to_response(tree_data: Dict[str, Any]) -> ProjectTreeResponse:
    """
    Recursively maps tree data to ProjectTreeResponse.
    """
    children = []
    if "children" in tree_data:
        children = [
            map_tree_to_response(child) for child in tree_data["children"]
        ]
   
    return ProjectTreeResponse(
        key=tree_data.get("_key", tree_data.get("key", "")),
        name=tree_data.get("name", ""),
        icon=tree_data.get("icon", ""),
        description=tree_data.get("description", ""),
        node_type=tree_data.get("node_type", ""),
        qname=tree_data.get("qname", ""),
        properties=tree_data.get("properties", {}),
        theme=tree_data.get("theme", {}),
        children=children
    )


def get_manager() -> CodeGraphManager:
    """Dependency to get the CodeGraphManager."""
    # In a real application, this could be a more complex dependency,
    # e.g., creating a new manager instance per request or using a singleton.
    return CodeGraphManager()


router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(
    project: ProjectCreate,
    manager: CodeGraphManager = Depends(get_manager)
):
    """
    Create a new project.
    """

    scanner = ProjectScanner(project.path, project.name)
    scanner.scan()
    new_project_node = scanner.get_project()
    project_response = ProjectResponse(
        key=new_project_node.key,
        name=new_project_node.name,
        path=new_project_node.path
    )

    return project_response


@router.get("/{project_key}", response_model=ProjectResponse)
def get_project(
    project_key: str,
    manager: CodeGraphManager = Depends(get_manager)
):
    """
    Retrieve a single project by its key.
    """
    project_node = manager.get_project(project_key)
    if not project_node:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(
        key=project_node.key,
        name=project_node.name,
        path=project_node.path
    )


@router.get("/{project_key}/virtual-folders",
            response_model=List[VirtualFolderResponse])
def get_project_virtual_folders(
    project_key: str,
    manager: CodeGraphManager = Depends(get_manager)
):
    """
    Retrieve all virtual folders for a project.
    """
    project_node = manager.get_project(project_key)
    if not project_node:
        raise HTTPException(status_code=404, detail="Project not found")
    return [
        folder.get_descendant_tree()
        for folder in project_node.get_virtual_folders()
    ]


@router.get("/{project_key}/tree", response_model=ProjectTreeResponse)
def get_project_tree(
    project_key: str,
    manager: CodeGraphManager = Depends(get_manager)
):
    """
    Retrieve project tree structure.
    """
    
    project_node = manager.get_project(project_key)
    if not project_node:
        raise HTTPException(status_code=404, detail="Project not found")

    tree_data = project_node.get_descendant_tree()
    return map_tree_to_response(tree_data)


@router.get("/", response_model=List[ProjectResponse])
def get_all_projects(manager: CodeGraphManager = Depends(get_manager)):
    """
    Retrieve all projects.
    """
    project_nodes = manager.get_all_projects()
    return [
        ProjectResponse(
            key=p.key,
            name=p.name,
            path=p.path
        ) for p in project_nodes
    ]


@router.put("/{project_key}", response_model=ProjectResponse)
def update_project(
    project_key: str,
    project: ProjectUpdate,
    manager: CodeGraphManager = Depends(get_manager)
):
    """
    Update a project's details.
    """
    updated_project_node = manager.get_project(project_key)
    if not updated_project_node:
        raise HTTPException(status_code=404, detail="Project not found")
    updated_project_node.update(name=project.name, path=project.path)
    return ProjectResponse(
        key=updated_project_node.key,
        name=updated_project_node.name,
        path=updated_project_node.path
    )


@router.delete("/{project_key}", status_code=204)
def delete_project(
    project_key: str,
    manager: CodeGraphManager = Depends(get_manager)
):
    """
    Delete a project by its key.
    """
    success = manager.delete_project(project_key)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return None
