from fastapi import APIRouter, Depends, HTTPException, Response
from app.core.manager import CodeGraphManager
from app.core.virtual_folder import VirtualFolder
from app.core.virtual_file import VirtualFile
from pydantic import BaseModel
from typing import Optional


class VirtualFileUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class VirtualFileCreate(BaseModel):
    name: str
    description: str | None = None
    parent_id: str | None = None
    project_id: str

class VirtualFileResponse(BaseModel):
    key: str
    name: str
    node_type: str
    qname: str
    description: str | None = None

def get_manager() -> CodeGraphManager:
    return CodeGraphManager()


router = APIRouter()




@router.post("/virtual-file", response_model=VirtualFileResponse, status_code=201)
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
    return VirtualFileResponse(
        key=new_file.key,
        name=new_file.name,
        node_type=new_file.model.node_type,
        qname=new_file.qname,
        description=new_file.description,
    )

@router.get("/virtual-file/{file_key}", response_model=VirtualFileResponse)
def get_virtual_file(
    file_key: str
):
    virtual_file = VirtualFile.get_by_key(file_key)
    if not virtual_file:
        raise HTTPException(status_code=404, detail="Virtual file not found")
    return VirtualFileResponse(
        key=virtual_file.key,
        name=virtual_file.name,
        node_type=virtual_file.model.node_type,
        qname=virtual_file.qname,
        description=virtual_file.description,
    )

@router.put("/virtual-file/{file_key}", response_model=VirtualFileResponse)
def update_virtual_file(
    file_key: str,
    file_update: VirtualFileUpdate,
):
    virtual_file = VirtualFile.get_by_key(file_key)
    if not virtual_file:
        raise HTTPException(status_code=404, detail="Virtual file not found")
    updated_file = virtual_file.update(file_update.model_dump(exclude_unset=True)) 
    return VirtualFileResponse(
        key=updated_file.key,
        name=updated_file.name,
        node_type=updated_file.model.node_type,
        qname=updated_file.qname,
        description=updated_file.description,
    )

@router.delete("/virtual-file/{file_key}", status_code=204)
def delete_virtual_file(
    file_key: str
):
    virtual_file = VirtualFile.get_by_key(file_key)
    if not virtual_file:
        raise HTTPException(status_code=404, detail="Virtual file not found")
    virtual_file.delete()
    return Response(status_code=204)