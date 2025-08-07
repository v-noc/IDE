from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from app.core.manager import CodeGraphManager
from app.core.code_elements import Function, Class
from app.core.virtual_folder import VirtualFolder
from typing import Dict, Any, Optional, List


# Pydantic Models
class VirtualFolderCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None


class VirtualFolderUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class VirtualFolderResponse(BaseModel):
    key: str
    name: str
    node_type: str
    qname: str
    description: Optional[str] = None
    link_to: Optional[Dict[str, Any]] = None
    children: List['VirtualFolderResponse'] = []
    call_order: Optional[int] = None
    imports: Optional[List[Dict[str, Any]]] = None


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


@router.post(
    "/virtual-folder",
    response_model=VirtualFolderResponse,
    status_code=201
)
def create_virtual_folder(
    project_key: str,
    request: VirtualFolderCreate,
    manager: CodeGraphManager = Depends(get_manager),
):
    """
    Creates a new virtual folder for a project.
    """
    project = manager.get_project(project_key)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if request.parent_id:
        parent_folder = VirtualFolder.get_by_key(request.parent_id)
        if not parent_folder:
            raise HTTPException(
                status_code=404, detail="Parent folder not found"
            )
        new_folder = parent_folder.add_virtual_folder(
            request.name, request.description
        )
    else:
        new_folder = project.add_virtual_folder(
            request.name, request.description
        )

    return new_folder.to_dict()


@router.put(
    "/virtual-folder/{folder_key}",
    response_model=VirtualFolderResponse
)
def update_virtual_folder(
    project_key: str,
    folder_key: str,
    request: VirtualFolderUpdate,
    manager: CodeGraphManager = Depends(get_manager),
):
    project = manager.get_project(project_key)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    folder = VirtualFolder.get_by_key(folder_key)
    if not folder:
        raise HTTPException(status_code=404, detail="Virtual folder not found")

    update_data = request.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    updated_folder = folder.update(update_data)
    return updated_folder.to_dict()


@router.get(
    "/virtual-folders",
    response_model=List[VirtualFolderResponse],
)
def get_all_virtual_folders(
    project_key: str,
    manager: CodeGraphManager = Depends(get_manager),
):
    """
    Gets all virtual folders for a project.
    """
    project = manager.get_project(project_key)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    virtual_folders = project.get_all_virtual_folders()
    return [folder.to_dict() for folder in virtual_folders]


@router.get(
    "/virtual-folder/{folder_key}",
    response_model=VirtualFolderResponse
)
def get_virtual_folder(
    project_key: str,
    folder_key: str,
    manager: CodeGraphManager = Depends(get_manager),
):
    """
    Gets a virtual folder by its key.
    """
    project = manager.get_project(project_key)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    folder = VirtualFolder.get_by_key(folder_key)
    if not folder:
        raise HTTPException(status_code=404, detail="Virtual folder not found")
    
    return folder.get_descendant_tree()


@router.post(
    "/virtual-folder/{folder_key}/add-code-element",
    response_model=VirtualFolderResponse,
    status_code=201
)
def add_code_element_to_virtual_folder(
    project_key: str,
    folder_key: str,
    request: AddCodeElementRequest,
    manager: CodeGraphManager = Depends(get_manager),
):
    """
    Adds a code element to a virtual folder.
    """
    folder = VirtualFolder.get_by_key(folder_key)
    if not folder:
        raise HTTPException(status_code=404, detail="Virtual folder not found")
    
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
        new_folder = folder.create_folder_for_element(element)
        return new_folder.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete(
    "/virtual-folder/{folder_key}/code-element/{element_key}",
    status_code=204
)
def remove_code_element_from_virtual_folder(
    project_key: str,
    folder_key: str,
    element_key: str,
    manager: CodeGraphManager = Depends(get_manager),
):
    """
    Removes a code element from a virtual folder.
    """
    project = manager.get_project(project_key)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    folder = VirtualFolder.get_by_key(folder_key)
    if not folder:
        raise HTTPException(status_code=404, detail="Virtual folder not found")

    element_node = manager.get_node(element_key)
    if not element_node:
        raise HTTPException(status_code=404, detail="Code element not found")

    if element_node.node_type not in ['function', 'class']:
        raise HTTPException(
            status_code=400,
            detail="Only functions and classes can be removed."
        )

    try:
        if folder.remove_element_by_id(element_node.id):
            return Response(status_code=204)
        else:
            raise HTTPException(
                status_code=404,
                detail="Element not found in virtual folder"
            )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post(
    "/virtual-folder/create-path/{element_key}",
    status_code=201,
)
def create_path_for_element(
    project_key: str,
    element_key: str,
    request: VirtualFolderCreate,
    
    manager: CodeGraphManager = Depends(get_manager),
):
    """
    Creates a path for a code element.
    """
    project = manager.get_project(project_key)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    element_node = manager.get_node(element_key)
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
        folder = project.add_virtual_folder(
            request.name, request.description
        )
        new_folder = folder.create_folder_for_element(
            element, link_directly=True
        )
        return new_folder.to_dict()
    except Exception as e:
        raise HTTPException(status_code=409, detail=str(e))

