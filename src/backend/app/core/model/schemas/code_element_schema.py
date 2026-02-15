
from typing import Optional, Set

from app.core.model.nodes import ClassNode, FunctionNode

from .base import BaseSchema
from .metadata import CodePositionSchema, DocumentSchema, ThemeConfigSchema


class CodeElementGroupSchema(BaseSchema):
    """
    The schema for the code element group document.
    """

    class_children: Set["ClassSchema"]
    function_children: Set["FunctionSchema"]
    code_element_group: Set["CodeElementGroupSchema"]
    theme_config: Optional[ThemeConfigSchema]


class CallGroupSchema(BaseSchema):
    """
    The schema for the call group document.
    """

    call_children: Set["CallSchema"]
    call_group: Set["CallGroupSchema"]
    theme_config: Optional[ThemeConfigSchema]


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
    code_position: CodePositionSchema
    theme_config: Optional[ThemeConfigSchema]
    documents: Set[DocumentSchema]
    base_classes: Set[str]

    @staticmethod
    def from_pydantic(class_node: ClassNode):
        by_type = class_node.get_children_by_type()
        return ClassSchema(
            _id=class_node.id,
            name=class_node.name,
            description=class_node.description,
            qname=class_node.qname,
            documents=class_node.documents,
            base_classes=class_node.base_classes,
            class_children=by_type.get("class_children", set()),
            function_children=by_type.get("function_children", set()),
            call_children=by_type.get("call_children", set()),
            code_element_group=by_type.get("code_element_group", set()),
            call_group=by_type.get("call_group", set()),
            code_position=CodePositionSchema.from_pydantic(
                class_node.code_position),
            theme_config=ThemeConfigSchema.from_pydantic(
                class_node.theme_config),
            created_at=class_node.created_at,
            updated_at=class_node.updated_at,
        )

    def to_pydantic(self):
        children = self.class_children | self.function_children | self.call_children | self.code_element_group | self.call_group
        children_by_type = {
            "class_children": self.class_children,
            "function_children": self.function_children,
            "call_children": self.call_children,
            "code_element_group": self.code_element_group,
            "call_group": self.call_group,
        }
        return ClassNode(
            id=self._id,
            name=self.name,
            qname=self.qname,
            description=self.description,
            code_position=self.code_position.to_pydantic(),
            theme_config=self.theme_config.to_pydantic() if self.theme_config else None,
            documents=self.documents,
            children=children,
            children_by_type=children_by_type,
            base_classes=self.base_classes,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


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
    documents: Set[DocumentSchema]
    code_position: CodePositionSchema
    theme_config: Optional[ThemeConfigSchema]

    @staticmethod
    def from_pydantic(function: FunctionNode):
        by_type = function.get_children_by_type()
        return FunctionSchema(
            _id=function.id,
            name=function.name,
            qname=function.qname,
            description=function.description,
            code_position=CodePositionSchema.from_pydantic(
                function.code_position),
            theme_config=ThemeConfigSchema.from_pydantic(
                function.theme_config),
            # children
            function_children=by_type.get("function_children", set()),
            class_children=by_type.get("class_children", set()),
            call_children=by_type.get("call_children", set()),
            code_element_group=by_type.get("code_element_group", set()),
            call_group=by_type.get("call_group", set()),
            # documents
            documents=function.documents,
            created_at=function.created_at,
            updated_at=function.updated_at,
        )

    def to_pydantic(self):

        children = self.function_children | self.class_children | self.call_children | self.code_element_group | self.call_group
        children_by_type = {
            "function_children": self.function_children,
            "class_children": self.class_children,
            "call_children": self.call_children,
            "code_element_group": self.code_element_group,
            "call_group": self.call_group,
        }
        return FunctionNode(
            id=self._id,
            name=self.name,
            qname=self.qname,
            description=self.description,
            code_position=self.code_position.to_pydantic(),
            theme_config=self.theme_config.to_pydantic() if self.theme_config else None,
            documents=self.documents,
            children=children,
            children_by_type=children_by_type,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class CallSchema(BaseSchema):
    """
    The schema for the call document.
    """

    call_children: Set["CallSchema"]
    target_function: "FunctionSchema"
    call_group: Set["CallGroupSchema"]
    theme_config: Optional[ThemeConfigSchema]
