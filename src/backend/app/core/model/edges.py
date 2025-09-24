from typing import Literal
from .base import BaseEdge

from pydantic import ConfigDict, Field
from .properties import CodePosition


class ContainsEdge(BaseEdge):
    edge_type: str = "contains_edges"

    # NEW: Differentiates the type of containment relationship.
    contain_type: Literal[
        "project_to_folder",
        "project_to_file",
        "folder_to_folder",
        "folder_to_file",

        # Code element relationships
        "file_to_class",
        "file_to_function",
        "class_to_class",
        "class_to_function",
        "function_to_function",
        "function_to_class",

        # Call relationships
        "file_to_call",
        "class_to_call",
        "function_to_call",
        "call_to_call",  # For nested calls e.g. foo(bar())
    ] = Field(..., description="The specific type of containment.")


class TargetsEdge(BaseEdge):
    edge_type: str = "targets_edges"
