from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class ArangoBase(BaseModel):
    """
    The base model for all ArangoDB documents. It defines the system
    attributes `_key` and `_id`, allowing them to be used as standard
    Pydantic fields `key` and `id`.
    """
    key: Optional[str] = Field(None, alias='_key')
    id: Optional[str] = Field(None, alias='_id')

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            # Add any custom JSON encoders if needed
        },
    )

class BaseNode(ArangoBase):
    """
    A base model for all node documents, ensuring a 'node_type' field
    is always present to distinguish between different types of nodes
    in the 'nodes' collection.
    """
    node_type: str

class BaseEdge(ArangoBase):
    """
    A base model for all edge documents. It includes the mandatory
    `_from` and `_to` fields required by ArangoDB for linking documents.
    """
    from_id: str = Field(..., alias='_from')
    to_id: str = Field(..., alias='_to')
    edge_type: str
