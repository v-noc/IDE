from pydantic import BaseModel, Field
from typing import Optional

class BaseDocument(BaseModel):
    key: Optional[str] = Field(None, alias="_key")
