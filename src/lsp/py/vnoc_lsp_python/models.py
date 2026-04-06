from typing import List, Literal, Optional

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
    children: List["BaseNode"] = Field(default_factory=list)


class CallNode(BaseNode):
    type: Literal["call"] = "call"
    call_index: int = 0
    call_col_pos: int = 0


class FunctionNode(BaseNode):
    type: Literal["function"] = "function"


class ClassNode(BaseNode):
    type: Literal["class"] = "class"
    base_classes: List[str] = Field(default_factory=list)


BaseNode.model_rebuild()
