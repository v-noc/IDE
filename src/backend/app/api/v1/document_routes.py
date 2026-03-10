from app.api.dependencies import get_document_service
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import Optional, Dict

from app.core.services.document_service import DocumentService
from app.core.model import DocumentNode
from pydantic import BaseModel, Field
from typing import List

router = APIRouter()


class DocumentResponse(DocumentNode):
    status: str = Field(default="unchanged")
    compare_to: Optional[DocumentNode] = None


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
    existing = await document_service.get(document_id)

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

    response = await document_service.update(existing)

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
        await document_service.delete(document_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    return None


@router.get("/", response_model=List[DocumentResponse])
async def get_documents_for_node(
    node_id: str = Query(...,
                         description="The ID of the node to get documents for"),
    document_service: DocumentService = Depends(get_document_service),
):

    try:
        documents = await document_service.get_nodes_by_parent_node(node_id)
        if document_service.uow.has_compare_to():
            compare_to_documents = await document_service.get_nodes_by_parent_node(node_id, compare_to=True)
            compare_by_id: Dict[str, DocumentNode] = {
                doc.id: doc for doc in compare_to_documents
            }
            merged_documents: List[DocumentResponse] = []

            # Current docs: mark added if missing in compare_to, otherwise attach compare_to.
            for doc in documents:
                compare_doc = compare_by_id.pop(doc.id, None)
                merged_documents.append(
                    DocumentResponse(
                        **doc.model_dump(),
                        status="added" if compare_doc is None else "unchanged",
                        compare_to=compare_doc,
                    )
                )

            # Docs that exist only in compare_to: emit synthetic removed docs.
            for compare_doc in compare_by_id.values():
                merged_documents.append(
                    DocumentResponse(
                        **compare_doc.model_dump(),
                        data="",
                        status="removed",
                        compare_to=compare_doc,
                    )
                )

            return merged_documents

        return [
            DocumentResponse(
                **doc.model_dump(),
                status="unchanged",
                compare_to=None,
            )
            for doc in documents
        ]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
