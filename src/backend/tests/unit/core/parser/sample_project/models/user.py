# src/backend/tests/unit/core/parser/sample_project/models/user.py
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str
    age: int = Field(default=18)
    def get_name(self) -> str:
        return self.name
