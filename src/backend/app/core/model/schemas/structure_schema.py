
from typing import Optional, Set

from app.db.schema.schema import LexicalKey
from app.core.model.nodes import FolderNode

from .base import BaseSchema
from .code_element_schema import (
    CallGroupSchema,
    CodeElementGroupSchema,
    ClassSchema,
    FunctionSchema,
    CallSchema)


class StructureGroupSchema(BaseSchema):
    """
    The schema for the structure group document.
    """
    folder_children: Set["FolderSchema"]
    file_children: Set["FileSchema"]
    structure_group: Set["StructureGroupSchema"]


class FileSchema(BaseSchema):
    """
    The schema for the file document.
    """
    qname: str
    path: str
    class_children: Set["ClassSchema"]
    function_children: Set["FunctionSchema"]
    code_element_group: Set["CodeElementGroupSchema"]
    call_group: Set["CallGroupSchema"]
    call_children: Set["CallSchema"]


class FolderSchema(BaseSchema):
    """
    The schema for the folder document.
    """
    qname: str
    path: str
    folder_children: Set["FolderSchema"]
    file_children: Set["FileSchema"]
    structure_group: Set["StructureGroupSchema"]

    @staticmethod
    def from_pydantic(folder: FolderNode):
        return FolderSchema(
            _id=folder.id,
            name=folder.name,
            description=folder.description,
            qname=folder.qname,
            path=folder.path,
            folder_children=folder.folder_children,
            file_children=folder.file_children,
            structure_group=folder.structure_group,
            created_at=folder.created_at,
            updated_at=folder.updated_at,
        )

    def to_pydantic(self):
        return FolderNode(
            id=self._id,
            name=self.name,
            description=self.description,
            qname=self.qname,
            path=self.path,
            folder_children=self.folder_children,
            file_children=self.file_children,
            structure_group=self.structure_group,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class ProjectSchema(BaseSchema):
    """
    The schema for the project document.
    """

    db_name: str
    local_path: str
    remote_path: Optional[str]
