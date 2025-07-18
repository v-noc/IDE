from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class BaseDocument(BaseModel):
    """
    A base model for all document collections in ArangoDB.
    Includes common audit fields and the document key.
    """
    key: Optional[str] = Field(None, alias="_key", description="The unique key of the document.")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="The timestamp when the document was created.")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="The timestamp when the document was last updated.")

class BaseEdge(BaseDocument):
    """
    A base model for all edge collections in ArangoDB.
    Includes the mandatory _from and _to fields for linking documents.
    """
    from_doc_id: str = Field(..., alias="_from", description="The document ID of the source of the edge.")
    to_doc_id: str = Field(..., alias="_to", description="The document ID of the destination of the edge.")
