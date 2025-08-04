from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.manager import CodeGraphManager
from app.core.code_elements import Function, Class
from app.models.node import FolderNode, VirtualFolderNode
from typing import List, Dict, Any, Optional, Union


# Pydantic Models
class VirtualFolderCreate(BaseModel):
    name: str
    description: str | None = None
    parent_id: str | None = None
    project_id: str
class VirtualFolderResponse(BaseModel):
    key: str
    name: str
    node_type: str
    qname: str
    description: str | None = None
    # children: List["VirtualFolderResponse"]

class VirtualFolderUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class LinkFileRequest(BaseModel):
    file_id: str

class AddCodeElementRequest(BaseModel):
    element_id: str
    target_virtual_file_id: Optional[str] = None
    virtual_file_name: Optional[str] = None
    include_dependencies: bool = True

class AddMultipleCodeElementsRequest(BaseModel):
    element_ids: List[str]
    include_dependencies: bool = True

class CodeElementSummaryResponse(BaseModel):
    functions: List[Dict[str, str]]
    classes: List[Dict[str, str]]
    packages: List[Dict[str, str]]
    total_count: int
    virtual_file: Optional[Dict[str, str]] = None

class MultipleCodeElementsResponse(BaseModel):
    virtual_files_created: List[Dict[str, str]]
    total_elements_added: int
    elements_by_file: Dict[str, Dict[str, Any]]

class VirtualFolderTreeResponse(BaseModel):
    key: str
    name: str
    node_type: str
    qname: str
    properties: dict
    children: List["VirtualFolderTreeResponse"]


# Helper Functions
def get_manager() -> CodeGraphManager:
    return CodeGraphManager()


def map_tree_to_response(
    tree_data: Dict[str, Any]
) -> VirtualFolderTreeResponse:
    """
    Recursively maps tree data to VirtualFolderTreeResponse.
    """
    children = []
    if "children" in tree_data and tree_data["children"]:
        children = [
            map_tree_to_response(child) for child in tree_data["children"]
        ]

    return VirtualFolderTreeResponse(
        key=tree_data.get("_key", tree_data.get("key", "")),
        name=tree_data.get("name", ""),
        node_type=tree_data.get("node_type", ""),
        qname=tree_data.get("qname", ""),
        properties=tree_data.get("properties", {}),
        children=children,
    )


router = APIRouter()


@router.post(
    "/virtual-folder",
    response_model=VirtualFolderResponse,
    status_code=201
)
def create_virtual_folder(
    folder: VirtualFolderCreate,
    manager: CodeGraphManager = Depends(get_manager)
):
    """
    Creates a new virtual folder.
    """
    project = manager.get_project(folder.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Assumes a 'create_virtual_folder' method on the manager.

    new_folder = manager.create_virtual_folder(
        project_id=folder.project_id,
        folder_name=folder.name,
        description=folder.description,
        parent_id=folder.parent_id,
    )

    if not new_folder:
        raise HTTPException(
            status_code=500, detail="Failed to create virtual folder"
        )

    return VirtualFolderResponse(
        key=new_folder.key,
        name=new_folder.name,
        node_type=new_folder.model.node_type,
        qname=new_folder.qname,
        description=new_folder.description,
        #   children=[]
    )


@router.get("/virtual-folder/{folder_key}", response_model=FolderNode)
def get_virtual_folder(
    folder_key: str, manager: CodeGraphManager = Depends(get_manager)
):
    """
    Retrieves a virtual folder by its key.
    """
    # Assumes a 'get_virtual_folder' method on the manager.
    virtual_folder = manager.get_virtual_folder(folder_key)
    if not virtual_folder:
        raise HTTPException(status_code=404, detail="Virtual folder not found")
    return virtual_folder.model


@router.put("/virtual-folder/{folder_key}", response_model=VirtualFolderResponse)
def update_virtual_folder(
    folder_key: str,
    folder_update: VirtualFolderUpdate,
    manager: CodeGraphManager = Depends(get_manager),
):
    """
    Updates a virtual folder's details.
    """
    # Assumes an 'update_virtual_folder' method on the manager.
    virtual_folder = manager.get_virtual_folder(folder_key)
    if not virtual_folder:
        raise HTTPException(status_code=404, detail="Virtual folder not found")
    updated_folder = virtual_folder.update(
        folder_update.model_dump(exclude_unset=True)
    )
    return updated_folder


@router.delete("/virtual-folder/{folder_key}", status_code=204)
def delete_virtual_folder(
    folder_key: str, manager: CodeGraphManager = Depends(get_manager)
):
    """
    Deletes a virtual folder.
    """
    # Assumes a 'delete_virtual_folder' method on the manager.
    virtual_folder = manager.get_virtual_folder(folder_key)
    if not virtual_folder:
        raise HTTPException(status_code=404, detail="Virtual folder not found")
    success = virtual_folder.delete()
    if not success:
        raise HTTPException(status_code=404, detail="Virtual folder not found")
    return None


@router.post("/virtual-folder/{folder_key}/files", status_code=201)
def add_file_to_virtual_folder(
    folder_key: str,
    request: LinkFileRequest,
    manager: CodeGraphManager = Depends(get_manager),
):
    """
    Adds (links) an existing file to a virtual folder.
    """
    # Assumes a 'link_file_to_virtual_folder' method on the manager.
    link_successful = manager.link_file_to_virtual_folder(
        virtual_folder_key=folder_key, file_id=request.file_id
    )
    if not link_successful:
        raise HTTPException(
            status_code=404, detail="Virtual folder or file not found"
        )
    return {"message": "File linked successfully"}

@router.post(
    "/virtual-folder/{folder_key}/add-code-element",
    response_model=CodeElementSummaryResponse,
    status_code=201
)
def add_code_element_to_virtual_folder(
    folder_key: str,
    request: AddCodeElementRequest,
    manager: CodeGraphManager = Depends(get_manager)
):
    """
    Adds a code element to a virtual folder, creating or using a virtual file.
    """
    virtual_folder = manager.get_virtual_folder(folder_key)
    if not virtual_folder:
        raise HTTPException(
            status_code=404, detail="Virtual folder not found"
        )
    
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
            detail="Only functions and classes can be added"
        )
    
    # Get target virtual file if specified
    target_virtual_file = None
    if request.target_virtual_file_id:
        from app.core.virtual_file import VirtualFile
        target_virtual_file = VirtualFile.get_by_key(
            request.target_virtual_file_id
        )
        if not target_virtual_file:
            raise HTTPException(
                status_code=404, detail="Target virtual file not found"
            )
    
    # Add the element with its dependencies
    result = virtual_folder.add_code_element_with_dependencies(
        element=element,
        target_virtual_file=target_virtual_file,
        virtual_file_name=request.virtual_file_name,
        include_dependencies=request.include_dependencies
    )
    
    return CodeElementSummaryResponse(**result)

@router.post(
    "/virtual-folder/{folder_key}/add-multiple-code-elements",
    response_model=MultipleCodeElementsResponse,
    status_code=201
)
def add_multiple_code_elements_to_virtual_folder(
    folder_key: str,
    request: AddMultipleCodeElementsRequest,
    manager: CodeGraphManager = Depends(get_manager)
):
    """
    Adds multiple code elements to separate virtual files in a folder.
    """
    virtual_folder = manager.get_virtual_folder(folder_key)
    if not virtual_folder:
        raise HTTPException(
            status_code=404, detail="Virtual folder not found"
        )
    
    # Get all code elements
    elements = []
    for element_id in request.element_ids:
        element_node = manager.get_node(element_id)
        if not element_node:
            raise HTTPException(
                status_code=404, 
                detail=f"Code element {element_id} not found"
            )
        
        if element_node.node_type == 'function':
            elements.append(Function(element_node))
        elif element_node.node_type == 'class':
            elements.append(Class(element_node))
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Element {element_id} is not a function or class"
            )
    
    # Add all elements to separate files
    result = virtual_folder.add_code_elements_to_separate_files(
        elements=elements,
        include_dependencies=request.include_dependencies
    )
    
    return MultipleCodeElementsResponse(**result)

@router.get(
    "/virtual-folder/{folder_key}/code-elements-summary",
    response_model=Dict[str, Any]
)
def get_virtual_folder_code_elements_summary(
    folder_key: str,
    manager: CodeGraphManager = Depends(get_manager)
):
    """
    Gets a summary of all code elements in all virtual files in the folder.
    """
    virtual_folder = manager.get_virtual_folder(folder_key)
    if not virtual_folder:
        raise HTTPException(
            status_code=404, detail="Virtual folder not found"
        )
    
    return virtual_folder.get_all_code_elements_summary()

@router.get(
    "/virtual-folder/{folder_key}/tree",
    response_model=VirtualFolderTreeResponse
)
def get_virtual_folder_tree(
    folder_key: str, manager: CodeGraphManager = Depends(get_manager)
):
    """
    Retrieves the descendant tree of a virtual folder.
    """
    # Assumes 'get_virtual_folder' returns a domain object 
    # with 'get_descendant_tree'.
    virtual_folder = manager.get_virtual_folder(folder_key)
    if not virtual_folder:
        raise HTTPException(status_code=404, detail="Virtual folder not found")

    tree_data = virtual_folder.get_descendant_tree()
    return map_tree_to_response(tree_data)

