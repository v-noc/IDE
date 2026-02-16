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
    FileNode,
)

# Field names for path queries
CODE_ELEMENT_FIELDS = (
    "function_children",
    "class_children",
    "call_children",
    "code_element_group",
    "call_group",
)

# Map child type names to schema field names
CODE_CHILD_TYPE_TO_FIELD = {
    "function": "function_children",
    "class": "class_children",
    "call": "call_children",
    "code_element_group": "code_element_group",
    "call_group": "call_group",
}

CODE_SET_FIELDS_TO_PRESERVE = [
    "function_children",
    "class_children",
    "call_children",
    "code_element_group",
    "call_group",
    "documents",
]
CODE_OPTIONAL_FIELDS_TO_PRESERVE = ["theme_config"]

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
    elif schema_type == "FileSchema":
        return FileNode.from_raw_dict(raw)
    return parse_code_element_child(raw)


def build_path_field_name(
    child_types: list[str],
    all_fields: tuple[str, ...],
    type_to_field: dict[str, str] | None = None,
) -> str:
    """
    Build the path field name string for WOQL path queries.
    If child_types is empty, returns all fields in OR format: "(a|b|c)".
    Otherwise returns the requested fields joined: "a|b".
    When type_to_field is provided, maps type names (e.g. "function") to field
    names (e.g. "function_children") before joining.
    """
    if len(child_types) == 0:
        return "(" + "|".join(all_fields) + ")"
    if type_to_field:
        fields = [type_to_field.get(t, t) for t in child_types]
        return "|".join(fields)
    return "|".join(child_types)
