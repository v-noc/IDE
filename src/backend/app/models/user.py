from pydantic import BaseModel, Field
from typing import Optional

class BaseDocument(BaseModel):
    key: Optional[str] = Field(None, alias="_key")

class User(BaseDocument):
    username: str
    email: str

class NewUser(BaseModel):
    username: str
    email: str

class UpdateUser(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
