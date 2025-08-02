from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.manager import CodeGraphManager
from app.models.node import FolderNode
from typing import List, Dict, Any, Optional


# Pydantic Models
class VirtualFolderCreate(BaseModel):
    name: str
    description: str | None = None
    parent_id: str | None = None
    project_id: str


class VirtualFolderUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class LinkFileRequest(BaseModel):
    file_id: str


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


@router.post("/virtual-folder", response_model=FolderNode, status_code=201)
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
        name=folder.name,
        parent_id=folder.parent_id,
        description=folder.description,
    )

    if not new_folder:
        raise HTTPException(
            status_code=500, detail="Failed to create virtual folder"
        )
    return new_folder.model


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


@router.put("/virtual-folder/{folder_key}", response_model=FolderNode)
def update_virtual_folder(
    folder_key: str,
    folder_update: VirtualFolderUpdate,
    manager: CodeGraphManager = Depends(get_manager),
):
    """
    Updates a virtual folder's details.
    """
    # Assumes an 'update_virtual_folder' method on the manager.
    updated_folder = manager.update_virtual_folder(
        folder_key, folder_update.model_dump(exclude_unset=True)
    )
    if not updated_folder:
        raise HTTPException(status_code=404, detail="Virtual folder not found")
    return updated_folder.model


@router.delete("/virtual-folder/{folder_key}", status_code=204)
def delete_virtual_folder(
    folder_key: str, manager: CodeGraphManager = Depends(get_manager)
):
    """
    Deletes a virtual folder.
    """
    # Assumes a 'delete_virtual_folder' method on the manager.
    success = manager.delete_virtual_folder(folder_key)
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

