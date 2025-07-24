"""
API endpoints for managing projects using the Domain API.
"""
from fastapi import APIRouter, Depends, HTTPException
from app.models.project import NewProject
from app.models.node import NodePosition
from app.core.manager import CodeGraphManager
from app.db.client import get_db
from arango.database import StandardDatabase

router = APIRouter()

def get_manager() -> CodeGraphManager:
    """Dependency to get the CodeGraphManager."""
    return CodeGraphManager()

@router.post("/projects/", status_code=201)
def create_project(project: NewProject, manager: CodeGraphManager = Depends(get_manager)):
    """
    Create a new project using the domain manager.
    """
    created_project = manager.create_project(
        name=project.name,
        path=f"/path/to/{project.name}", # Example path
        description=project.description
    )
    return {"message": f"Project '{created_project.name}' created.", "key": created_project.project_model.key}

@router.post("/projects/example", status_code=201)
def create_example_project(manager: CodeGraphManager = Depends(get_manager)):
    """
    An example endpoint demonstrating the power of the domain API to build a
    code graph with just a few lines of code.
    """
    # 1. Create a project
    project = manager.create_project(name="ExampleProject", path="/path/to/example")

    # 2. Add files and functions
    file_a = project.add_file("/path/to/example/file_a.py")
    func_x = file_a.add_function("function_x", NodePosition(line_no=1, col_offset=0, end_line_no=5, end_col_offset=10))
    
    file_b = project.add_file("/path/to/example/file_b.py")
    func_y = file_b.add_function("function_y", NodePosition(line_no=3, col_offset=0, end_line_no=8, end_col_offset=20))

    # 3. Create a relationship between them
    func_x.add_call(func_y, NodePosition(line_no=4, col_offset=4, end_line_no=4, end_col_offset=15))

    return {"message": "Example project created successfully."}


from app.services.validator import GraphValidator

@router.get("/projects/{project_key}/validate")
def validate_project(project_key: str, db: StandardDatabase = Depends(get_db)):
    """
    Validate the graph of a project.
    """
    validator = GraphValidator(db)
    report = validator.validate_project_graph(project_key)
    return report
