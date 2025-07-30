from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.manager import CodeGraphManager

from pydantic import BaseModel

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

  

def get_manager() -> CodeGraphManager:
    """Dependency to get the CodeGraphManager."""
    # In a real application, this could be a more complex dependency,
    # e.g., creating a new manager instance per request or using a singleton.
    return CodeGraphManager()

router = APIRouter()

@router.post("/project/", response_model=ProjectResponse, status_code=201)
def create_project(project: ProjectCreate, manager: CodeGraphManager = Depends(get_manager)):
    """
    Create a new project.
    """
    new_project_node = manager.create_project(name=project.name, path=project.path)
    return ProjectResponse(
        key=new_project_node.key,
        name=new_project_node.name,
        path=new_project_node.properties.path
    )

@router.get("/project/{project_key}", response_model=ProjectResponse)
def get_project(project_key: str, manager: CodeGraphManager = Depends(get_manager)):
    """
    Retrieve a single project by its key.
    """
    project_node = manager.get_project(project_key)
    if not project_node:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(
        key=project_node.key,
        name=project_node.name,
        path=project_node.properties.path
    )

@router.get("/projects", response_model=List[ProjectResponse])
def get_all_projects(manager: CodeGraphManager = Depends(get_manager)):
    """
    Retrieve all projects.
    """
    project_nodes = manager.get_all_projects()
    return [
        ProjectResponse(
            key=p.key,
            name=p.name,
            path=p.properties.path
        ) for p in project_nodes
    ]

@router.put("/projects/{project_key}", response_model=ProjectResponse)
def update_project(project_key: str, project: ProjectUpdate, manager: CodeGraphManager = Depends(get_manager)):
    """
    Update a project's details.
    """
    updated_project_node = manager.update_project(project_key, project.name, project.path)
    if not updated_project_node:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(
        key=updated_project_node.key,
        name=updated_project_node.name,
        path=updated_project_node.properties.path
    )

@router.delete("/projects/{project_key}", status_code=204)
def delete_project(project_key: str, manager: CodeGraphManager = Depends(get_manager)):
    """
    Delete a project by its key.
    """
    success = manager.delete_project(project_key)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return None
