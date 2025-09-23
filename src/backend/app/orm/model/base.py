from typing import Literal
from .properties import CodePosition
from pydantic import ConfigDict, Field
from .base import BaseEdge
from datetime import datetime, timezone

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal


class ArangoBase(BaseModel):
    """
    The base model for all ArangoDB documents. It defines the system
    attributes `_key` and `_id`, allowing them to be used as standard
    Pydantic fields `key` and `id`.
    """
    key: Optional[str] = Field(
        None, alias='_key', description="The key of the node.")
    id: Optional[str] = Field(
        None, alias='_id', description="The ID of the node.")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: (
                lambda dt: dt.astimezone(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
            ),
        },
    )


class BaseNode(ArangoBase):
    name: str = Field(..., description="The name of the node.", min_length=1)
    description: str = Field(...,
                             description="The description of the node.", min_length=1)
    qname: str = Field(...,
                       description="The qualified name of the node.", min_length=1)
    node_type: str = Field(..., description="The type of the node.")

    model_config = ConfigDict(
        populate_by_name=True,
        indexes=[
            {"fields": ["node_type", "qname"]},
        ],
    )


class BaseEdge(ArangoBase):
    from_id: str = Field(..., alias="_from",
                         description="The ID of the source node.")
    to_id: str = Field(..., alias="_to",
                       description="The ID of the target node.")
    edge_type: str = Field(..., description="The type of the edge.")

    model_config = ConfigDict(
        populate_by_name=True,
        indexes=[],
    )
