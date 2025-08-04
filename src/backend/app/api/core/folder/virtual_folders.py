from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.manager import CodeGraphManager
from app.core.code_elements import Function, Class
from typing import Dict, Any, Optional


# Pydantic Models
class VirtualFolderCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    project_id: str

class VirtualFolderResponse(BaseModel):
    key: str
    name: str
    node_type: str
    qname: str
    description: Optional[str] = None
    linked_element: Optional[Dict[str, Any]] = None

class AddCodeElementRequest(BaseModel):
    element_id: str
    parent_folder_key: str


router = APIRouter()

# Helper Functions
def get_manager() -> CodeGraphManager:
    return CodeGraphManager()


@router.post(
    "/virtual-folder/add-element",
    response_model=VirtualFolderResponse,
    status_code=201,
)
def add_element_as_virtual_folder(
    request: AddCodeElementRequest,
    manager: CodeGraphManager = Depends(get_manager),
):
    """
    Creates a new virtual folder for a code element and adds it as a child
    to the specified parent virtual folder.
    """
    parent_folder = manager.get_virtual_folder(request.parent_folder_key)
    if not parent_folder:
        raise HTTPException(
            status_code=404, detail="Parent virtual folder not found"
        )

    element_node = manager.get_node(request.element_id)
    if not element_node:
        raise HTTPException(status_code=404, detail="Code element not found")
    
    if element_node.node_type not in ['function', 'class']:
        raise HTTPException(
            status_code=400,
            detail="Only functions and classes can be added."
        )

    element = (
        Function(element_node) if element_node.node_type == 'function' 
        else Class(element_node)
    )
    
    try:
        new_folder = parent_folder.create_folder_for_element(element)
        return new_folder.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
