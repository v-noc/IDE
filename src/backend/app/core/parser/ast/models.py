from pydantic import BaseModel, Field
from typing import List, Optional, Union
from enum import Enum


class SchemaType(str, Enum):
    # Core tracking Schemas
    NAME = "name"
    ATTRIBUTE = "attribute"

    # Definition Schemas
    FUNCTION = "function"
    CLASS = "class"

    # Import Schemas
    IMPORT = "import"
    IMPORT_FROM = "import_from"
    IMPORT_ALIAS = "import_alias"

    # Usage Schemas
    CALL = "call"
    ASSIGN = "assign"
    ANN_ASSIGN = "ann_assign"

    # Function parts
    ARG = "arg"
    KEYWORD = "keyword"
    SUBSCRIPT = "subscript"


class SchemaPosition(BaseModel):
    line_no: int
    col_offset: int
    end_line_no: Optional[int] = None
    end_col_offset: Optional[int] = None


class BaseSchema(BaseModel):
    schema_type: SchemaType
    position: SchemaPosition


class ParentSchema(BaseSchema):
    children: List["BaseSchema"] = Field(default_factory=list)


# Core reference Schemas


class NameSchema(BaseSchema):
    schema_type: SchemaType = SchemaType.NAME
    name: str


class AttributeSchema(BaseSchema):
    schema_type: SchemaType = SchemaType.ATTRIBUTE
    name: str  # The attribute name (e.g., 'method' in obj.method)
    value: Optional[Union["NameSchema", "AttributeSchema", "CallSchema"]] = (
        None  # The object being accessed
    )


class SubscriptSchema(BaseSchema):
    """Represents a complex subscripted type like List[int] or Dict[str, User]"""

    schema_type: SchemaType = SchemaType.SUBSCRIPT
    # The full, readable string representation, e.g., "List[Union[s,b]]"
    full_str: str
    elements: List[Union[NameSchema, AttributeSchema]] = Field(
        default_factory=list
    )  # A flat list of all names found inside


# Import Schemas


class ImportAliasSchema(BaseSchema):
    schema_type: SchemaType = SchemaType.IMPORT_ALIAS
    name: str
    asname: Optional[str] = None


class ImportSchema(BaseSchema):
    schema_type: SchemaType = SchemaType.IMPORT
    names: List[ImportAliasSchema] = Field(default_factory=list)


class ImportFromSchema(BaseSchema):
    schema_type: SchemaType = SchemaType.IMPORT_FROM
    module_name: Optional[str] = None
    names: List[ImportAliasSchema] = Field(default_factory=list)
    level: int = 0


# Function/Class definition Schemas


class ArgSchema(BaseSchema):
    schema_type: SchemaType = SchemaType.ARG
    name: str
    annotation: Optional[Union[NameSchema, AttributeSchema, SubscriptSchema, str]] = (
        None
    )


class FunctionSchema(ParentSchema):
    schema_type: SchemaType = SchemaType.FUNCTION
    name: str
    id: Optional[str] = None
    args: List[ArgSchema] = Field(default_factory=list)
    return_annotation: Optional[
        Union[NameSchema, AttributeSchema, SubscriptSchema, str]
    ] = None
    return_values: List[Union[NameSchema, AttributeSchema, SubscriptSchema, str]] = (
        Field(default_factory=list)
    )
    decorator_list: List[Union[NameSchema, AttributeSchema]] = Field(
        default_factory=list
    )


class ClassSchema(ParentSchema):
    id: Optional[str] = None
    schema_type: SchemaType = SchemaType.CLASS
    name: str
    implements: List[Union[NameSchema, AttributeSchema]
                     ] = Field(default_factory=list)
    decorator_list: List[Union[NameSchema, AttributeSchema]] = Field(
        default_factory=list
    )


# Usage tracking Schemas


class KeywordSchema(BaseSchema):
    schema_type: SchemaType = SchemaType.KEYWORD
    name: str
    value: Optional[Union[NameSchema, AttributeSchema,
                          BaseSchema, str, object]] = None


class CallSchema(BaseSchema):
    schema_type: SchemaType = SchemaType.CALL
    func: Union[NameSchema, AttributeSchema,
                "BaseSchema"]  # Function being called
    args: List[Union[NameSchema, AttributeSchema, object]] = Field(
        default_factory=list
    )  # Only track name/attribute args
    keywords: List[KeywordSchema] = Field(default_factory=list)


class AssignSchema(BaseSchema):
    schema_type: SchemaType = SchemaType.ASSIGN
    targets: List[NameSchema | AttributeSchema] = Field(
        default_factory=list
    )  # Variables being assigned
    value: List[NameSchema | AttributeSchema | CallSchema | None] = Field(
        default_factory=list
    )


class AnnAssignSchema(BaseSchema):
    schema_type: SchemaType = SchemaType.ANN_ASSIGN
    target: NameSchema | AttributeSchema
    annotation: Union[NameSchema, AttributeSchema, SubscriptSchema, str]
    value: List[Union[NameSchema, AttributeSchema, CallSchema]] = Field(
        default_factory=list
    )
