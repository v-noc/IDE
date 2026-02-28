
from typing import Optional, Set

from app.core.model.nodes import CallNode, ClassNode, CodeElementGroupNode, FunctionNode

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
    documents: Set[DocumentSchema]

    @staticmethod
    def from_pydantic(code_element_group: CodeElementGroupNode):
        by_type = code_element_group.get_children_by_type()

        return CodeElementGroupSchema(
            _id=code_element_group.id,
            name=code_element_group.name,
            description=code_element_group.description,
            documents=code_element_group.documents,
            class_children=by_type.get("class_children", set()),
            function_children=by_type.get("function_children", set()),
            code_element_group=by_type.get("code_element_group", set()),
            theme_config=ThemeConfigSchema.from_pydantic(
                code_element_group.theme_config),
            created_at=code_element_group.created_at,
            updated_at=code_element_group.updated_at,
        )

    def to_pydantic(self):
        children = self.class_children | self.function_children | self.code_element_group
        children_by_type = {
            "class_children": self.class_children,
            "function_children": self.function_children,
            "code_element_group": self.code_element_group,
        }
        return CodeElementGroupNode(
            id=self._id,
            name=self.name,
            description=self.description,
            documents=self.documents,
            theme_config=self.theme_config.to_pydantic() if self.theme_config else None,
            children=children,
            children_by_type=children_by_type,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


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
    qname: str
    call_children: Set["CallSchema"]
    target_function: Optional["FunctionSchema"]
    target_class: Optional["ClassSchema"]
    call_group: Set["CallGroupSchema"]
    theme_config: Optional[ThemeConfigSchema]
    documents: Set[DocumentSchema]

    @classmethod
    def _to_dict(self, skip_checking=False):
        result = super()._to_dict(skip_checking=skip_checking)

        result.pop("target_function")
        result.pop("target_class")

        result["@oneOf"] = {

            "target_function": "FunctionSchema",
            "target_class": "ClassSchema",
        }

        return result

    @staticmethod
    def from_pydantic(call: CallNode):
        by_type = call.get_children_by_type()
        is_function = call.target_function.startswith(FunctionSchema.__name__)
        target_function = None
        target_class = None
        if is_function:
            target_function = call.target_function
        else:
            target_class = call.target_function
        return CallSchema(
            _id=call.id,
            name=call.name,
            qname=call.qname,
            description=call.description,
            target_function=target_function,
            target_class=target_class,
            call_children=by_type.get("call_children", set()),
            call_group=by_type.get("call_group", set()),
            theme_config=ThemeConfigSchema.from_pydantic(
                call.theme_config),
            documents=call.documents,

            created_at=call.created_at,
            updated_at=call.updated_at,
        )

    def to_pydantic(self):
        children = self.call_children | self.call_group
        children_by_type = {
            "call_children": self.call_children,
            "call_group": self.call_group,
        }
        return CallNode(
            id=self._id,
            name=self.name,
            qname=self.qname,
            description=self.description,
            target_function=self.target_function if self.target_function else self.target_class,
            children=children,
            children_by_type=children_by_type,
            documents=self.documents,
            theme_config=self.theme_config.to_pydantic() if self.theme_config else None,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
