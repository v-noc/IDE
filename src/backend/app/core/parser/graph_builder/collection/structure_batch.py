from dataclasses import dataclass, field
from typing import List, Tuple

from app.core.model.nodes import FileNode, FolderNode


@dataclass
class StructureBatchPlan:
    insert: List[FolderNode | FileNode] = field(default_factory=list)
    update: List[FolderNode | FileNode] = field(default_factory=list)
    delete: List[str] = field(default_factory=list)
    move: List[Tuple[str, str, str]] = field(default_factory=list)

    def extend(self, other: "StructureBatchPlan") -> None:
        self.insert.extend(other.insert)
        self.update.extend(other.update)
        self.delete.extend(other.delete)
        self.move.extend(other.move)
