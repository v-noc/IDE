from typing import List
from pydantic import Field

from app.core.model.logs import LogNode


class LogTreeNode(LogNode):
    children: List["LogTreeNode"] = Field(
        default_factory=list, description="Log children."
    )


LogTreeNode.model_rebuild()
