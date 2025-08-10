from fastapi import APIRouter, Depends, HTTPException, Response
from app.core.manager import CodeGraphManager
from app.core.virtual_folder import VirtualFolder
from app.core.virtual_file import VirtualFile
from app.core.code_elements import Function, Class
from pydantic import BaseModel
from typing import Optional, Dict, Any


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

class AddCodeElementRequest(BaseModel):
    element_id: str
    include_dependencies: bool = True

class CodeElementSummaryResponse(BaseModel):
    functions: list[Dict[str, str]]
    classes: list[Dict[str, str]]
    packages: list[Dict[str, str]]
    total_count: int

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

@router.post(
    "/virtual-file/{file_key}/add-code-element", 
    response_model=CodeElementSummaryResponse,
    status_code=201
)
def add_code_element_to_virtual_file(
    file_key: str,
    request: AddCodeElementRequest,
    manager: CodeGraphManager = Depends(get_manager)
):
    """
    Adds a code element (function or class) to a virtual file with its 
    dependencies.
    """
    virtual_file = VirtualFile.get_by_key(file_key)
    if not virtual_file:
        raise HTTPException(status_code=404, detail="Virtual file not found")
    
    # Get the code element
    element_node = manager.get_node(request.element_id)
    if not element_node:
        raise HTTPException(status_code=404, detail="Code element not found")
    
    # Create appropriate domain object
    if element_node.node_type == 'function':
        element = Function(element_node)
    elif element_node.node_type == 'class':
        element = Class(element_node)
    else:
        raise HTTPException(
            status_code=400, 
            detail="Only functions and classes can be added to virtual files"
        )
    
    # Add the element with its dependencies
    result = virtual_file.add_code_element_with_dependencies(
        element=element,
        include_dependencies=request.include_dependencies
    )
    
    return CodeElementSummaryResponse(**result)

@router.delete(
    "/virtual-file/{file_key}/code-element/{element_id}", 
    status_code=204
)
def remove_code_element_from_virtual_file(
    file_key: str,
    element_id: str
):
    """
    Removes a code element from a virtual file.
    """
    virtual_file = VirtualFile.get_by_key(file_key)
    if not virtual_file:
        raise HTTPException(status_code=404, detail="Virtual file not found")
    
    success = virtual_file.remove_code_element(element_id)
    if not success:
        raise HTTPException(
            status_code=404, 
            detail="Code element not found in virtual file"
        )
    
    return Response(status_code=204)

@router.get(
    "/virtual-file/{file_key}/code-elements", 
    response_model=CodeElementSummaryResponse
)
def get_virtual_file_code_elements(file_key: str):
    """
    Gets all code elements contained in a virtual file.
    """
    virtual_file = VirtualFile.get_by_key(file_key)
    if not virtual_file:
        raise HTTPException(status_code=404, detail="Virtual file not found")
    
    summary = virtual_file.get_code_elements_summary()
    return CodeElementSummaryResponse(**summary)