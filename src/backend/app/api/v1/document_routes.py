from app.api.dependencies import get_document_service
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import Optional

from app.core.services.document_service import DocumentService
from app.core.repository import Repositories
from app.db.client import get_terminus_client
from arangoasync.database import AsyncDatabase
from app.core.model import DocumentNode
from pydantic import BaseModel, Field
from typing import List

router = APIRouter()


class CreateDocumentRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    node_id: str = Field(..., min_length=1)


class UpdateDocumentRequest(BaseModel):
    node_id: str = Field(..., min_length=1)
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, min_length=1)
    data: Optional[str] = None


@router.post(
    "/",
    response_model=DocumentNode,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    request: CreateDocumentRequest,
    document_service: DocumentService = Depends(get_document_service),
):
    try:
        response = await document_service.create(
            name=request.name,
            description=request.description,
            node_id=request.node_id,
        )

        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put("/", response_model=DocumentNode)
async def update_document(
    document_id: str = Query(...,
                             description="The ID of the document to update"),
    document_service: DocumentService = Depends(get_document_service),
    request: UpdateDocumentRequest = Body(...),
):
    is_root = False
    if request.node_id.startswith("ProjectSchema/"):
        is_root = True
    existing = await document_service.get(document_id, is_root=is_root)

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    if request.name is not None:
        existing.name = request.name
    if request.description is not None:
        existing.description = request.description
    if request.data is not None:
        existing.data = request.data

    response = await document_service.update(existing, is_root=is_root)

    return response


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str = Query(...,
                             description="The ID of the document to delete"),
    node_id: str = Query(
        ...,
        min_length=1,
        description="Parent node key or id",
    ),
    document_service: DocumentService = Depends(get_document_service),
):
    try:
        is_root = False
        if node_id.startswith("ProjectSchema/"):
            is_root = True
        await document_service.delete(document_id, is_root=is_root)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    return None


@router.get("/", response_model=List[DocumentNode])
async def get_documents_for_node(
    node_id: str = Query(...,
                         description="The ID of the node to get documents for"),
    document_service: DocumentService = Depends(get_document_service),
):
    print(f"node_id: {node_id}")
    try:
        documents = await document_service.get_nodes_by_parent_node(node_id)
        print(f"documents: {documents}")
        return documents
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
