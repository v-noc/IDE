
from typing import Optional, Set

from app.db.schema.schema import LexicalKey
from app.core.model.nodes import FileNode, FolderNode, StructureGroupNode

from .base import BaseSchema


from .code_element_schema import (
    CallGroupSchema,
    CodeElementGroupSchema,
    ClassSchema,
    FunctionSchema,
    CallSchema)
from .metadata import DocumentSchema, ThemeConfigSchema


class CodeContentSchema(BaseSchema):
    """
    Schema for storing file content separately from FileSchema.
    One CodeContent per file, linked via file reference.
    """
    file: "FileSchema"
    content: str

    @staticmethod
    def from_file_content(file_id: str, content: str) -> "CodeContentSchema":
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        # Deterministic id for upsert: CodeContentSchema/file_id_safe
        safe_id = file_id.replace("/", "_")
        content_id = f"CodeContentSchema/{safe_id}"
        return CodeContentSchema(
            _id=content_id,
            name="CodeContent",
            description="File content",
            file=file_id,
            content=content,
            created_at=now,
            updated_at=now,
        )


class StructureGroupSchema(BaseSchema):
    """
    The schema for the structure group document.
    """
    folder_children: Set["FolderSchema"]
    file_children: Set["FileSchema"]
    structure_group: Set["StructureGroupSchema"]
    documents: Set[DocumentSchema]
    theme_config: Optional[ThemeConfigSchema]

    @staticmethod
    def from_pydantic(structure_group: StructureGroupNode):
        by_type = structure_group.get_children_by_type()
        return StructureGroupSchema(
            _id=structure_group.id,
            name=structure_group.name,
            description=structure_group.description,
            folder_children=by_type.get("folder_children", set()),
            file_children=by_type.get("file_children", set()),
            structure_group=by_type.get("structure_group", set()),
            documents=structure_group.documents,
            theme_config=ThemeConfigSchema.from_pydantic(
                structure_group.theme_config),
            created_at=structure_group.created_at,
            updated_at=structure_group.updated_at,
        )

    def to_pydantic(self):
        return StructureGroupNode(
            id=self._id,
            name=self.name,
            description=self.description,
            children=self.folder_children | self.file_children | self.structure_group or set(),
            children_by_type={
                "folder_children": self.folder_children or set(),
                "file_children": self.file_children or set(),
                "structure_group": self.structure_group or set(),
            },
            documents=self.documents or set(),
            theme_config=self.theme_config.to_pydantic() if self.theme_config else None,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


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


INIT_FOLDER_ID = "FolderSchema/init"


class FolderSchema(BaseSchema):
    """
    The schema for the folder document.
    """
    qname: str
    path: str
    folder_children: Set["FolderSchema"]
    is_root: bool
    file_children: Set["FileSchema"]
    structure_group: Set["StructureGroupSchema"]
    documents: Set[DocumentSchema]
    theme_config: Optional[ThemeConfigSchema]

    @staticmethod
    def create_init_folder() -> "FolderSchema":
        """Create the global document theme folder (is_root=True)."""
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        return FolderSchema(
            _id=INIT_FOLDER_ID,
            name="__init__",
            description="Global document theme folder",
            qname="__init__",
            path="/",
            folder_children=set(),
            file_children=set(),
            structure_group=set(),
            documents=set(),
            theme_config=None,
            is_root=True,
            created_at=now,
            updated_at=now,
        )

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
            is_root=folder.is_root,
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
            is_root=self.is_root,
        )


class ProjectSchema(BaseSchema):
    """
    The schema for the project document.
    """

    db_name: str
    local_path: str
    remote_path: Optional[str]

    theme_config: Optional[ThemeConfigSchema]
