from typing import Optional, Set
from .base import BaseSchema
from .code_element_schema import ClassSchema, FunctionSchema
from .structure_schema import FileSchema


class TestConfigSchema(BaseSchema):
    """
    The schema for the test configuration.
    """
    enabled: bool
    test_root: str
    test_args: str


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
