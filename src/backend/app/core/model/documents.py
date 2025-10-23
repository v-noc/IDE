from enum import Enum
from .base import ArangoBase
from pydantic import BaseModel, Field
from typing import List


class DocumentNode(ArangoBase):
    name: str = Field(..., description="The name of the document.")
    description: str = Field(...,
                             description="The description of the document.")

    data: str = Field(..., description="The data of the document.")
