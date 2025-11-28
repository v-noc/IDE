from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List

class ScopeType(str, Enum):
    FOLDER = "folder"
    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"

class ScopeModel(BaseModel):
    id: str
    name: str
    qname: str  # Qualified name, e.g., "file.py::MyClass::my_method"
    type: ScopeType
    file_path: str
    start_line: int
    start_col: int
    end_line: int
    end_col: int
    base_classes: List[str] = Field(default_factory=list)  # For CLASS type
    mro: List[str] = Field(default_factory=list)  # Method Resolution Order for CLASS type

class CallSiteModel(BaseModel):
    id: str
    line: int
    col: int
