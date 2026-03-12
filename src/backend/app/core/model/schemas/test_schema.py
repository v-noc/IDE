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
    target_function: Optional[FunctionSchema]
    target_class: Optional[ClassSchema]
    target_file: Optional[FileSchema]


class TestCaseSchema(BaseSchema):
    """
    The schema for the test case.
    """
    name: str
    description: str
    test_config: Optional[TestConfigSchema]
    test_links: Set[TestLinkSchema]
