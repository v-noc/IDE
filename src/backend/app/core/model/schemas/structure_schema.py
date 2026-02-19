
from typing import Optional, Set

from app.db.schema.schema import LexicalKey
from app.core.model.nodes import FileNode, FolderNode

from .base import BaseSchema
from .code_element_schema import (
    CallGroupSchema,
    CodeElementGroupSchema,
    ClassSchema,
    FunctionSchema,
    CallSchema)
from .metadata import DocumentSchema, ThemeConfigSchema


class StructureGroupSchema(BaseSchema):
    """
    The schema for the structure group document.
    """
    folder_children: Set["FolderSchema"]
    file_children: Set["FileSchema"]
    structure_group: Set["StructureGroupSchema"]
    documents: Set[DocumentSchema]
    theme_config: Optional[ThemeConfigSchema]


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
    documents: Set[DocumentSchema]
    theme_config: Optional[ThemeConfigSchema]
    hash: str

    @staticmethod
    def from_pydantic(file: FileNode):
        by_type = file.get_children_by_type()

        return FileSchema(
            _id=file.id,
            name=file.name,
            description=file.description,
            qname=file.qname,
            path=file.path,
            hash=file.hash,
            class_children=by_type.get("class_children", set()),
            function_children=by_type.get("function_children", set()),
            code_element_group=by_type.get("code_element_group", set()),
            call_group=by_type.get("call_group", set()),
            call_children=by_type.get("call_children", set()),
            created_at=file.created_at,
            documents=file.documents,
            theme_config=ThemeConfigSchema.from_pydantic(file.theme_config),
            updated_at=file.updated_at,
        )

    def to_pydantic(self):
        return FileNode(
            id=self._id,
            name=self.name,
            description=self.description,
            qname=self.qname,
            path=self.path,
            hash=self.hash,
            documents=self.documents or set(),
            theme_config=self.theme_config.to_pydantic() if self.theme_config else None,
            children=self.class_children | self.function_children | self.code_element_group
            | self.call_group | self.call_children,
            children_by_type={
                "class_children": self.class_children,
                "function_children": self.function_children,
                "code_element_group": self.code_element_group,
                "call_group": self.call_group,
                "call_children": self.call_children,
            },
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class FolderSchema(BaseSchema):
    """
    The schema for the folder document.
    """
    qname: str
    path: str
    folder_children: Set["FolderSchema"]
    file_children: Set["FileSchema"]
    structure_group: Set["StructureGroupSchema"]
    documents: Set[DocumentSchema]
    theme_config: Optional[ThemeConfigSchema]

    @staticmethod
    def from_pydantic(folder: FolderNode):
        by_type = folder.get_children_by_type()
        return FolderSchema(
            _id=folder.id,
            name=folder.name,
            description=folder.description,
            qname=folder.qname,
            path=folder.path,
            folder_children=by_type.get("folder_children", set()),
            file_children=by_type.get("file_children", set()),
            structure_group=by_type.get("structure_group", set()),
            created_at=folder.created_at,
            documents=folder.documents,
            theme_config=ThemeConfigSchema.from_pydantic(folder.theme_config),
            updated_at=folder.updated_at,
        )

    def to_pydantic(self):
        return FolderNode(
            id=self._id,
            name=self.name,
            description=self.description,
            qname=self.qname,
            path=self.path,
            children=self.folder_children | self.file_children | self.structure_group,
            children_by_type={
                "folder_children": self.folder_children,
                "file_children": self.file_children,
                "structure_group": self.structure_group,
            },
            documents=self.documents or set(),
            theme_config=self.theme_config.to_pydantic() if self.theme_config else None,
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
