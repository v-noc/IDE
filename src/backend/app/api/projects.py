"""
API endpoints for managing projects.
"""
from fastapi import APIRouter, Depends, HTTPException
from ...models.project import Project, NewProject
from ...db.service import DatabaseService, db_service
from ...graph.builder import GraphBuilder
from ...graph.validator import GraphValidator

router = APIRouter()

@router.post("/projects/", response_model=Project, status_code=201)
def create_project(project: NewProject, db: DatabaseService = Depends(get_db_service)):
    """
    Create a new project.
    """
    new_project = Project(**project.model_dump())
    created_project = db.projects.create(new_project)
    return created_project

@router.get("/projects/{project_key}", response_model=Project)
def get_project(project_key: str, db: DatabaseService = Depends(get_db_service)):
    """
    Get a project by its key.
    """
    project = db.projects.get(project_key)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("/projects/{project_key}/scan", status_code=202)
def scan_project(project_key: str, db: DatabaseService = Depends(get_db_service)):
    """
    Trigger a graph build for a project.
    This is an asynchronous task.
    """
    project = db.projects.get(project_key)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # In a real application, this would be sent to a background worker (e.g., Celery).
    # For this example, we run it synchronously.
    graph_builder = GraphBuilder(db)
    graph_builder.build_graph_for_project(project)
    
    return {"message": "Project scan initiated."}

@router.get("/projects/{project_key}/validate")
def validate_project(project_key: str, db: DatabaseService = Depends(get_db_service)):
    """
    Validate the graph of a project.
    """
    project = db.projects.get(project_key)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    validator = GraphValidator(db)
    report = validator.validate_project_graph(project_key)
    return report

# Helper dependency
def get_db_service():
    return db_service
