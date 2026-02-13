
from typing import Optional, Set

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


class ProjectSchema(BaseSchema):
    """
    The schema for the project document.
    """
    db_name: str
    local_path: str
    remote_path: str
