"""
Helpers for parsing raw child documents from repository queries into Node types.
"""

from typing import Any, Optional

from app.core.model.nodes import (
    FunctionNode,
    ClassNode,
    CallNode,
    CodeElementGroupNode,
    CallGroupNode,
    FolderNode,
)

# Field names for path queries
CODE_ELEMENT_FIELDS = (
    "function_children",
    "class_children",
    "call_children",
    "code_element_group",
    "call_group",
)

STRUCTURE_FIELDS = (
    "folder_children",
    "file_children",
    "structure_group",
)


def parse_code_element_child(raw: dict[str, Any]) -> Optional[Any]:
    """
    Convert a raw child document to the appropriate code element Node based on
    @type. Returns FunctionNode, ClassNode, CallNode, CodeElementGroupNode, or
    CallGroupNode. Returns None if the schema type is not recognized.
    """
    schema_type = raw.get("@type")
    parsers = {
        "FunctionSchema": FunctionNode.from_raw_dict,
        "ClassSchema": ClassNode.from_raw_dict,
        "CallSchema": CallNode.from_raw_dict,
        "CodeElementGroupSchema": CodeElementGroupNode.from_raw_dict,
        "CallGroupSchema": CallGroupNode.from_raw_dict,
    }
    parser = parsers.get(schema_type)
    return parser(raw) if parser else None


def parse_structure_child(raw: dict[str, Any]) -> Optional[FolderNode]:
    """
    Convert a raw child document to the appropriate structure Node based on
    @type. Currently supports FolderSchema -> FolderNode.
    Returns None if the schema type is not recognized.
    """
    schema_type = raw.get("@type")
    if schema_type == "FolderSchema":
        return FolderNode.from_raw_dict(raw)
    return None


def build_path_field_name(
    child_types: list[str],
    all_fields: tuple[str, ...],
) -> str:
    """
    Build the path field name string for WOQL path queries.
    If child_types is empty, returns all fields in OR format: "(a|b|c)".
    Otherwise returns the requested fields joined: "a|b".
    """
    if len(child_types) == 0:
        return "(" + "|".join(all_fields) + ")"
    return "|".join(child_types)
