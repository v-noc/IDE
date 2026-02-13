
from grp import struct_group

from httpx._transports import default
from .properties import CodePosition, ThemeConfig

from datetime import datetime
from typing import List, Optional, Set, Union
from pydantic import Field

from pydantic import BaseModel, Field


class BaseNode(BaseModel):
    id: Optional[str] = Field(..., description="The ID of the node.")
    name: str = Field(..., description="The name of the node.")
    description: str = Field(..., description="The description of the node.")
    created_at: datetime = Field(...,
                                 description="The creation time of the node.")
    updated_at: datetime = Field(...,
                                 description="The update time of the node.")


class DocumentNode(BaseNode):
    data: str = Field(..., description="The data of the document.")


class ProjectNode(BaseNode):
    local_path: str = Field(..., description="The local path of the project.")
    remote_path: Optional[str] = Field(default=None,
                                       description="The remote path of the project.", )
    db_name: str = Field(..., description="The name of the database.")


class CodeElementGroupNode(BaseNode):
    class_children: Set[Union[str, "ClassNode"]] = Field(
        default=set(), description="The children of the code element group.")
    function_children: Set[Union[str, "FunctionNode"]] = Field(
        default=set(), description="The children of the code element group.")
    theme_config: Optional[ThemeConfig] = Field(
        default=None, description="The theme config of the code element group.")
    documents: Set[Union[str, "DocumentNode"]] = Field(
        default=set(), description="The documents of the code element group.")


class CallGroupNode(BaseNode):
    call_children: Set[Union[str, "CallNode"]] = Field(
        default=set(), description="The children of the call group.")
    code_element_group: Set[Union[str, "CodeElementGroupNode"]] = Field(
        default=set(), description="The children of the call group.")
    theme_config: Optional[ThemeConfig] = Field(
        default=None, description="The theme config of the call group.")
    documents: Set[Union[str, "DocumentNode"]] = Field(
        default=set(), description="The documents of the call group.")


class StructureGroupNode(BaseNode):
    folder_children: Set[Union[str, "FolderNode"]] = Field(
        default=set(), description="The children of the structure group.")
    file_children: Set[Union[str, "FileNode"]] = Field(
        default=set(), description="The children of the structure group.")
    structure_group: Set[Union[str, "StructureGroupNode"]] = Field(
        default=set(), description="The children of the group.")
    theme_config: Optional[ThemeConfig] = Field(
        default=None, description="The theme config of the structure group.")
    documents: Set[Union[str, "DocumentNode"]] = Field(
        default=set(), description="The documents of the structure group.")


class FolderNode(BaseNode):
    path: str = Field(..., description="The path of the folder.")
    qname: str = Field(..., description="The qname of the folder.")
    structure_group: Set[Union[str, "StructureGroupNode"]] = Field(
        default=set(), description="The children of the folder.")
    folder_children: Set[Union[str, "FolderNode"]] = Field(
        default=set(), description="The children of the folder.")
    file_children: Set[Union[str, "FileNode"]] = Field(
        default=set(), description="The children of the folder.")
    theme_config: Optional[ThemeConfig] = Field(
        default=None, description="The theme config of the folder.")
    documents: Set[Union[str, "DocumentNode"]] = Field(
        default=set(), description="The documents of the folder.")

    @staticmethod
    def from_raw_dict(raw_dict):
        return FolderNode(
            id=raw_dict["@id"],
            name=raw_dict["name"],
            description=raw_dict["description"],
            qname=raw_dict["qname"],
            path=raw_dict["path"],
            folder_children=raw_dict.get(
                "folder_children", set()),
            file_children=raw_dict.get("file_children", set()),
            structure_group=raw_dict.get(
                "structure_group", set()),
            created_at=raw_dict["created_at"],
            updated_at=raw_dict["updated_at"],

        )


class CallContainerNode(BaseNode):
    call_children: Set[Union[str, "CallNode"]] = Field(
        default=set(), description="The children of the call container.")

    call_group: Set[Union[str, "CallGroupNode"]] = Field(
        default=set(), description="The children of the call container.")


class CodeElementContainerNode(BaseNode):
    class_children: Set[Union[str, "ClassNode"]] = Field(
        default=set(), description="The children of the file.")
    function_children: Set[Union[str, "FunctionNode"]] = Field(
        default=set(), description="The children of the file.")
    code_element_group: Set[Union[str, "CodeElementGroupNode"]] = Field(
        default=set(), description="The children of the file.")


class FileNode(CodeElementContainerNode, CallContainerNode):
    path: str = Field(..., description="The path of the file.")
    qname: str = Field(..., description="The qname of the file.")

    theme_config: Optional[ThemeConfig] = Field(
        default=None, description="The theme config of the file.")
    documents: Set[Union[str, "DocumentNode"]] = Field(
        default=set(), description="The documents of the file.")
    hash: str = Field(..., description="The hash of the file.")


class ClassNode(CodeElementContainerNode, CallContainerNode):
    qname: str = Field(..., description="The qname of the class.")

    code_position: CodePosition = Field(...,
                                        description="The code position of the class.")
    theme_config: Optional[ThemeConfig] = Field(
        default=None, description="The theme config of the class.")
    documents: Set[Union[str, "DocumentNode"]] = Field(
        default=set(), description="The documents of the class.")


class FunctionNode(CodeElementContainerNode, CallContainerNode):
    qname: str = Field(..., description="The qname of the class.")
    code_position: CodePosition = Field(...,
                                        description="The code position of the class.")
    theme_config: Optional[ThemeConfig] = Field(
        default=None, description="The theme config of the class.")
    documents: Set[Union[str, "DocumentNode"]] = Field(
        default=set(), description="The documents of the class.")


class CallNode(CallContainerNode):
    qname: str = Field(..., description="The qname of the call.")
    target_function: "FunctionNode" = Field(
        ..., description="The target function of the call.")

    theme_config: Optional[ThemeConfig] = Field(
        default=None, description="The theme config of the call.")
    documents: Set[Union[str, "DocumentNode"]] = Field(
        default=set(), description="The documents of the call.")
