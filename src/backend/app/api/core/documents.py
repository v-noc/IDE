from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from app.core.services.document_service import DocumentService
from app.core.repository import Repositories
from app.db.client import get_db
from arango.database import StandardDatabase
from app.core.model.documents import DocumentNode
from pydantic import BaseModel, Field
from typing import List

router = APIRouter()


def get_document_service(
    db: StandardDatabase = Depends(get_db),
) -> DocumentService:
    repos = Repositories(db)
    return DocumentService(repos)


class CreateDocumentRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    node_id: str = Field(..., min_length=1)


class UpdateDocumentRequest(BaseModel):
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
        return await document_service.create(
            name=request.name,
            description=request.description,
            node_id=request.node_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put("/{document_key}", response_model=DocumentNode)
async def update_document(
    document_key: str,
    request: UpdateDocumentRequest,
    document_service: DocumentService = Depends(get_document_service),
):
    existing = await document_service.get(document_key)

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_key} not found",
        )

    if request.name is not None:
        existing.name = request.name
    if request.description is not None:
        existing.description = request.description
    if request.data is not None:
        existing.data = request.data

    return await document_service.update(existing)


@router.delete("/{document_key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_key: str,
    node_id: str = Query(
        ...,
        min_length=1,
        description="Parent node key or id",
    ),
    document_service: DocumentService = Depends(get_document_service),
):
    try:
        await document_service.delete(document_key, node_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    return None


@router.get("/{node_id}", response_model=List[DocumentNode])
async def get_documents_for_node(
    node_id: str,
    document_service: DocumentService = Depends(get_document_service),
):
    try:
        documents = await document_service.get_nodes_by_parent_node(node_id)
        return documents
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
