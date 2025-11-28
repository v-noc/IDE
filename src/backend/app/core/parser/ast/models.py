from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class NodePosition(BaseModel):
    line: int
    column: int
    end_line: int
    end_column: int

class BaseNode(BaseModel):
    id: Optional[str] = None
    name: str
    type: Literal["class", "function", "call"]
    position: NodePosition
    # We don't necessarily need children on BaseNode if CallNode doesn't have them, 
    # but it's easier for polymorphism.
    children: List["BaseNode"] = Field(default_factory=list)

class CallNode(BaseNode):
    type: Literal["call"] = "call"
    # Call might not have an ID in the same way as defs, but we can keep it consistent.
    # It usually doesn't have children we care about for this specific task (unless nested calls?)
    # The user said "only class function and call position".
    # We'll keep children empty for calls usually.

class FunctionNode(BaseNode):
    type: Literal["function"] = "function"

class ClassNode(BaseNode):
    type: Literal["class"] = "class"
