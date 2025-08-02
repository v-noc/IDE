from fastapi import APIRouter, Depends, HTTPException
from app.core.manager import CodeGraphManager
from app.models.node import  VirtualFileNode
from pydantic import BaseModel





class VirtualFileCreate(BaseModel):
    name: str
    description: str | None = None
    parent_id: str | None = None
    project_id: str


def get_manager() -> CodeGraphManager:
    return CodeGraphManager()


router = APIRouter()




@router.post("/virtual-file", response_model=VirtualFileNode, status_code=201)
def create_virtual_file(
    file: VirtualFileCreate,
    manager: CodeGraphManager = Depends(get_manager)
):
    project = manager.get_project(file.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not file.parent_id:
        raise HTTPException(
            status_code=400, detail="Virtual file must have a parent."
        )

    parent_folder = manager.get_virtual_folder(file.parent_id)
    if not parent_folder:
        raise HTTPException(
            status_code=404, detail="Parent virtual folder not found"
        )

    new_file = parent_folder.add_virtual_file(file.name, file.description)
    return new_file.model
