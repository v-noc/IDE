from typing import Optional, Set
from .base import BaseSchema
from .code_element_schema import ClassSchema, FunctionSchema
from .structure_schema import FileSchema


def _test_case_id(target_function_id: str) -> str:
    safe_target = target_function_id.replace("/", "_")
    return f"TestCaseSchema/{safe_target}"


def _test_link_id(test_case_id: str, owner_node_id: str) -> str:
    safe_case = test_case_id.replace("/", "_")
    safe_owner = owner_node_id.replace("/", "_")
    return f"TestLinkSchema/{safe_case}___{safe_owner}"


class TestConfigSchema(BaseSchema):
    """
    The schema for the test configuration.
    """
    enabled: bool
    test_root: str
    test_args: str
    executable_path: Optional[str] = None


class TestLinkSchema(BaseSchema):
    """
    The schema for the test link.
    """
    lines: Set[int]
    owner_function: Optional[FunctionSchema]
    owner_class: Optional[ClassSchema]
    owner_file: Optional[FileSchema]


class TestCaseSchema(BaseSchema):
    """
    The schema for the test case.
    """
    name: str
    description: str
    node_id: str
    path: str
    target_function: Optional[FunctionSchema]
    test_links: Set[TestLinkSchema]
