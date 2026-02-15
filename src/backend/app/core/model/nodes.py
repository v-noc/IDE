from .properties import CodePosition, ThemeConfig

from datetime import datetime, timezone
from typing import Optional, Set
from pydantic import BaseModel, Field


def _merge_children(raw_dict: dict, keys: tuple[str, ...]) -> set:
    """Merge multiple child keys from raw_dict into a single set."""
    result: set = set()
    for key in keys:
        result.update(raw_dict.get(key, set()) or set())
    return result


def _children_by_type(raw_dict: dict, key_to_field: tuple[tuple[str, str], ...]) -> dict[str, set]:
    """Extract children by type from raw_dict for schema persistence."""
    return {
        field: set(raw_dict.get(key, set()) or set())
        for key, field in key_to_field
    }


class BaseNode(BaseModel):
    id: Optional[str] = Field(..., description="The ID of the node.")
    name: str = Field(..., description="The name of the node.")
    description: str = Field(..., description="The description of the node.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),
                                 description="The creation time of the node.")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),
                                 description="The update time of the node.")

    @staticmethod
    def from_raw_dict(raw_dict):
        return BaseNode(
            id=raw_dict["@id"],
            name=raw_dict["name"],
            description=raw_dict["description"],
            created_at=raw_dict["created_at"],
            updated_at=raw_dict["updated_at"],
        )


class DocumentNode(BaseNode):
    data: str = Field(..., description="The data of the document.")


class ProjectNode(BaseNode):
    local_path: str = Field(..., description="The local path of the project.")
    remote_path: Optional[str] = Field(default=None,
                                       description="The remote path of the project.", )
    db_name: str = Field(..., description="The name of the database.")


class CodeElementGroupNode(BaseNode):
    children: Set[str] = Field(
        default_factory=set, description="The children of the code element group."
    )
    documents: Set[str] = Field(
        default_factory=set, description="The documents of the code element group."
    )
    theme_config: Optional[ThemeConfig] = Field(
        default=None, description="The theme config of the code element group.")

    @staticmethod
    def from_raw_dict(raw_dict):
        base = BaseNode.from_raw_dict(raw_dict)
        return CodeElementGroupNode(
            **base.model_dump(),
            children=_merge_children(
                raw_dict,
                ("class_children", "function_children"),
            ),
            documents=raw_dict.get("documents", set()) or set(),
            theme_config=raw_dict.get("theme_config"),
        )


class CallGroupNode(BaseNode):
    children: Set[str] = Field(
        default_factory=set, description="The children of the call group."
    )
    documents: Set[str] = Field(
        default_factory=set, description="The documents of the call group."
    )
    theme_config: Optional[ThemeConfig] = Field(
        default=None, description="The theme config of the call group.")

    @staticmethod
    def from_raw_dict(raw_dict):
        base = BaseNode.from_raw_dict(raw_dict)
        return CallGroupNode(
            **base.model_dump(),
            children=_merge_children(
                raw_dict,
                ("call_children", "code_element_group"),
            ),
            documents=raw_dict.get("documents", set()) or set(),
            theme_config=raw_dict.get("theme_config"),
        )


class StructureGroupNode(BaseNode):
    children: Set[str] = Field(
        default_factory=set, description="The children of the structure group."
    )
    documents: Set[str] = Field(
        default_factory=set, description="The documents of the structure group."
    )
    theme_config: Optional[ThemeConfig] = Field(
        default=None, description="The theme config of the structure group.")

    @staticmethod
    def from_raw_dict(raw_dict):
        base = BaseNode.from_raw_dict(raw_dict)
        return StructureGroupNode(
            **base.model_dump(),
            children=_merge_children(
                raw_dict,
                ("folder_children", "file_children", "structure_group"),
            ),
            documents=raw_dict.get("documents", set()) or set(),
            theme_config=raw_dict.get("theme_config"),
        )


# Keys for schema persistence (raw_dict key -> schema field name)
_FOLDER_CHILDREN_KEYS = (
    ("folder_children", "folder_children"),
    ("file_children", "file_children"),
    ("structure_group", "structure_group"),
)
_CODE_ELEMENT_CHILDREN_KEYS = (
    ("class_children", "class_children"),
    ("function_children", "function_children"),
    ("code_element_group", "code_element_group"),

)
_CALL_CHILDREN_KEYS = (
    ("call_children", "call_children"),
    ("call_group", "call_group"),
)


_FILE_CHILDREN_KEYS = (_CODE_ELEMENT_CHILDREN_KEYS + _CALL_CHILDREN_KEYS)


class FolderNode(BaseNode):
    path: str = Field(..., description="The path of the folder.")
    qname: str = Field(..., description="The qname of the folder.")
    children: Set[str] = Field(
        default_factory=set, description="The children of the folder."
    )
    documents: Set[str] = Field(
        default_factory=set, description="The documents of the folder."
    )
    children_by_type: Optional[dict[str, set]] = Field(
        default=None,
        description="Split by type for schema persistence (folder_children, file_children, structure_group).",
    )
    theme_config: Optional[ThemeConfig] = Field(
        default=None, description="The theme config of the folder.")

    @staticmethod
    def from_raw_dict(raw_dict):
        base = BaseNode.from_raw_dict(raw_dict)
        by_type = _children_by_type(raw_dict, _FOLDER_CHILDREN_KEYS)
        return FolderNode(
            **base.model_dump(),
            qname=raw_dict["qname"],
            path=raw_dict["path"],
            children=_merge_children(
                raw_dict,
                ("folder_children", "file_children", "structure_group"),
            ),
            documents=raw_dict.get("documents", set()) or set(),
            children_by_type=by_type,
            theme_config=raw_dict.get("theme_config"),
        )

    def get_children_by_type(self) -> dict[str, set]:
        """Return children split by type for schema persistence."""
        if self.children_by_type is not None:
            return self.children_by_type
        return dict.fromkeys(
            ("folder_children", "file_children", "structure_group"), set()
        )


class FileNode(BaseNode):
    path: str = Field(..., description="The path of the file.")
    qname: str = Field(..., description="The qname of the file.")
    documents: Set[str] = Field(
        default_factory=set, description="The documents of the file."
    )
    theme_config: Optional[ThemeConfig] = Field(
        default=None, description="The theme config of the file.")
    hash: str = Field(..., description="The hash of the file.")
    children_by_type: Optional[dict[str, set]] = Field(
        default=None,
        description="Split by type for schema persistence.",
    )
    children: Set[str] = Field(
        default_factory=set, description="The children of the file."
    )

    @staticmethod
    def from_raw_dict(raw_dict):
        base = BaseNode.from_raw_dict(raw_dict)
        children = _merge_children(
            raw_dict,
            ("class_children", "function_children",
             "code_element_group", "call_children", "call_group"),
        )

        by_type = _children_by_type(raw_dict, _FILE_CHILDREN_KEYS)
        return FileNode(
            **base.model_dump(),
            qname=raw_dict["qname"],
            path=raw_dict["path"],

            hash=raw_dict["hash"],
            children=children,
            documents=raw_dict.get("documents", set()) or set(),
            children_by_type=by_type,
            theme_config=raw_dict.get("theme_config"),
        )

    def get_children_by_type(self) -> dict[str, set]:
        """Return children split by type for schema persistence."""
        if self.children_by_type is not None:
            return self.children_by_type
        return dict.fromkeys(
            ("class_children", "function_children",
             "code_element_group", "call_children", "call_group"),
            set(),
        )


class ClassNode(BaseNode):
    qname: str = Field(..., description="The qname of the class.")
    code_position: CodePosition = Field(...,
                                        description="The code position of the class.")
    documents: Set[str] = Field(
        default_factory=set, description="The documents of the class."
    )
    children_by_type: Optional[dict[str, set]] = Field(
        default=None,
        description="Split by type for schema persistence.",
    )
    children: Set[str] = Field(
        default_factory=set, description="The children of the class."
    )
    base_classes: Set[str] = Field(
        default_factory=set, description="The base classes of the class.")
    theme_config: Optional[ThemeConfig] = Field(
        default=None, description="The theme config of the class.")

    @staticmethod
    def from_raw_dict(raw_dict):
        base = BaseNode.from_raw_dict(raw_dict)
        children = _merge_children(
            raw_dict,
            (
                "class_children",
                "function_children",
                "code_element_group",
                "call_children",
                "call_group",
            ),
        )
        by_type = _children_by_type(raw_dict, _CODE_ELEMENT_CHILDREN_KEYS)
        return ClassNode(
            **base.model_dump(),
            qname=raw_dict["qname"],
            code_position=raw_dict["code_position"],
            children=children,
            base_classes=raw_dict.get("base_classes", set()) or set(),
            children_by_type=by_type,
            documents=raw_dict.get("documents", set()) or set(),
            theme_config=raw_dict.get("theme_config"),
        )

    def get_children_by_type(self) -> dict[str, set]:
        """Return children split by type for schema persistence."""
        if self.children_by_type is not None:
            return self.children_by_type
        return dict.fromkeys(
            ("class_children", "function_children",
             "code_element_group", "call_children", "call_group"),
            set(),
        )


class FunctionNode(BaseNode):
    qname: str = Field(..., description="The qname of the function.")
    code_position: CodePosition = Field(...,
                                        description="The code position of the function.")

    children_by_type: Optional[dict[str, set]] = Field(
        default=None,
        description="Split by type for schema persistence.",
    )
    children: Set[str] = Field(
        default_factory=set, description="The children of the function."
    )
    documents: Set[str] = Field(
        default_factory=set, description="The documents of the function."
    )
    theme_config: Optional[ThemeConfig] = Field(
        default=None, description="The theme config of the function.")

    @staticmethod
    def from_raw_dict(raw_dict):
        base = BaseNode.from_raw_dict(raw_dict)
        children = _merge_children(
            raw_dict,
            (
                "class_children",
                "function_children",
                "code_element_group",
                "call_children",
                "call_group",
            ),
        )
        by_type = _children_by_type(raw_dict, _CODE_ELEMENT_CHILDREN_KEYS)
        return FunctionNode(
            **base.model_dump(),
            qname=raw_dict["qname"],
            code_position=raw_dict["code_position"],
            children=children,
            children_by_type=by_type,
            documents=raw_dict.get("documents", set()) or set(),
            theme_config=raw_dict.get("theme_config"),
        )

    def get_children_by_type(self) -> dict[str, set]:
        """Return children split by type for schema persistence."""
        if self.children_by_type is not None:
            return self.children_by_type
        return dict.fromkeys(
            ("class_children", "function_children",
             "code_element_group", "call_children", "call_group"),
            set(),
        )


class CallNode(BaseNode):
    qname: str = Field(..., description="The qname of the call.")
    target_function: str = Field(
        ..., description="The target function of the call.")
    children_by_type: Optional[dict[str, set]] = Field(
        default=None,
        description="Split by type for schema persistence.",
    )
    children: Set[str] = Field(
        default_factory=set, description="The children of the call."
    )
    documents: Set[str] = Field(
        default_factory=set, description="The documents of the call."
    )
    theme_config: Optional[ThemeConfig] = Field(
        default=None, description="The theme config of the call.")

    @staticmethod
    def from_raw_dict(raw_dict):
        base = BaseNode.from_raw_dict(raw_dict)
        children = _merge_children(
            raw_dict,
            ("call_children", "call_group"),
        )
        by_type = _children_by_type(raw_dict, _CALL_CHILDREN_KEYS)
        return CallNode(
            **base.model_dump(),
            qname=raw_dict["qname"],
            target_function=raw_dict["target_function"],
            children=children,
            children_by_type=by_type,
            documents=raw_dict.get("documents", set()) or set(),
            theme_config=raw_dict.get("theme_config"),
        )

    def get_children_by_type(self) -> dict[str, set]:
        """Return children split by type for schema persistence."""
        if self.children_by_type is not None:
            return self.children_by_type
        return dict.fromkeys(
            ("call_children", "call_group"),
            set(),
        )
