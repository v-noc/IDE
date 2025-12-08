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
    call_index: int = 0  # Order of the call trailer within a chained expression


class FunctionNode(BaseNode):
    type: Literal["function"] = "function"


class ClassNode(BaseNode):
    type: Literal["class"] = "class"
