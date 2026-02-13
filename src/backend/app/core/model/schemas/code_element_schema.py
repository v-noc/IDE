
from typing import Optional, Set

from .base import BaseSchema
from .metadata import CodePosition, ThemeConfig


class CodeElementGroupSchema(BaseSchema):
    """
    The schema for the code element group document.
    """

    class_children: Set["ClassSchema"]
    function_children: Set["FunctionSchema"]
    code_element_group: Set["CodeElementGroupSchema"]
    theme_config: Optional[ThemeConfig]


class CallGroupSchema(BaseSchema):
    """
    The schema for the call group document.
    """

    call_children: Set["CallSchema"]
    call_group: Set["CallGroupSchema"]
    theme_config: Optional[ThemeConfig]


class ClassSchema(BaseSchema):
    """
    The schema for the class document.
    """
    qname: str
    class_children: Set["ClassSchema"]
    function_children: Set["FunctionSchema"]
    call_children: Set["CallSchema"]
    code_element_group: Set["CodeElementGroupSchema"]
    call_group: Set["CallGroupSchema"]
    code_position: CodePosition
    theme_config: Optional[ThemeConfig]


class FunctionSchema(BaseSchema):
    """
    The schema for the function document.
    """
    qname: str
    function_children: Set["FunctionSchema"]
    class_children: Set["ClassSchema"]
    call_children: Set["CallSchema"]
    code_element_group: Set["CodeElementGroupSchema"]
    call_group: Set["CallGroupSchema"]
    code_position: CodePosition
    theme_config: Optional[ThemeConfig]


class CallSchema(BaseSchema):
    """
    The schema for the call document.
    """

    call_children: Set["CallSchema"]
    target_function: "FunctionSchema"
    call_group: Set["CallGroupSchema"]
    theme_config: Optional[ThemeConfig]
