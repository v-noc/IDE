from copy import copy
from dataclasses import dataclass, is_dataclass
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
)

from fastapi._compat import shared
from fastapi.openapi.constants import REF_PREFIX as REF_PREFIX
from fastapi.types import ModelNameMap
from pydantic.version import VERSION as PYDANTIC_VERSION
from typing_extensions import Literal

PYDANTIC_VERSION_MINOR_TUPLE = tuple(int(x) for x in PYDANTIC_VERSION.split(".")[:2])
PYDANTIC_V2 = PYDANTIC_VERSION_MINOR_TUPLE[0] == 2
# Keeping old "Required" functionality from Pydantic V1, without
# shadowing typing.Required.
RequiredParam: Any = Ellipsis

if not PYDANTIC_V2:
    from pydantic import BaseConfig as BaseConfig
    from pydantic import BaseModel as BaseModel
    from pydantic import ValidationError as ValidationError
    from pydantic import create_model as create_model
    from pydantic.class_validators import Validator as Validator
    from pydantic.color import Color as Color
    from pydantic.error_wrappers import ErrorWrapper as ErrorWrapper
    from pydantic.errors import MissingError
    from pydantic.fields import (  # type: ignore[attr-defined]
        SHAPE_FROZENSET,
        SHAPE_LIST,
        SHAPE_SEQUENCE,
        SHAPE_SET,
        SHAPE_SINGLETON,
        SHAPE_TUPLE,
        SHAPE_TUPLE_ELLIPSIS,
    )
    from pydantic.fields import FieldInfo as FieldInfo
    from pydantic.fields import ModelField as ModelField  # type: ignore[attr-defined]
    from pydantic.fields import Undefined as Undefined  # type: ignore[attr-defined]
    from pydantic.fields import (  # type: ignore[attr-defined]
        UndefinedType as UndefinedType,
    )
    from pydantic.networks import AnyUrl as AnyUrl
    from pydantic.networks import NameEmail as NameEmail
    from pydantic.schema import TypeModelSet as TypeModelSet
    from pydantic.schema import (
        field_schema,
        model_process_schema,
    )
    from pydantic.schema import (
        get_annotation_from_field_info as get_annotation_from_field_info,
    )
    from pydantic.schema import get_flat_models_from_field as get_flat_models_from_field
    from pydantic.schema import (
        get_flat_models_from_fields as get_flat_models_from_fields,
    )
    from pydantic.schema import get_model_name_map as get_model_name_map
    from pydantic.types import SecretBytes as SecretBytes
    from pydantic.types import SecretStr as SecretStr
    from pydantic.typing import evaluate_forwardref as evaluate_forwardref
    from pydantic.utils import lenient_issubclass as lenient_issubclass


else:
    from pydantic.v1 import BaseConfig as BaseConfig  # type: ignore[assignment]
    from pydantic.v1 import BaseModel as BaseModel  # type: ignore[assignment]
    from pydantic.v1 import (  # type: ignore[assignment]
        ValidationError as ValidationError,
    )
    from pydantic.v1 import create_model as create_model  # type: ignore[no-redef]
    from pydantic.v1.class_validators import Validator as Validator
    from pydantic.v1.color import Color as Color  # type: ignore[assignment]
    from pydantic.v1.error_wrappers import ErrorWrapper as ErrorWrapper
    from pydantic.v1.errors import MissingError
    from pydantic.v1.fields import (
        SHAPE_FROZENSET,
        SHAPE_LIST,
        SHAPE_SEQUENCE,
        SHAPE_SET,
        SHAPE_SINGLETON,
        SHAPE_TUPLE,
        SHAPE_TUPLE_ELLIPSIS,
    )
    from pydantic.v1.fields import FieldInfo as FieldInfo  # type: ignore[assignment]
    from pydantic.v1.fields import ModelField as ModelField
    from pydantic.v1.fields import Undefined as Undefined
    from pydantic.v1.fields import UndefinedType as UndefinedType
    from pydantic.v1.networks import AnyUrl as AnyUrl
    from pydantic.v1.networks import (  # type: ignore[assignment]
        NameEmail as NameEmail,
    )
    from pydantic.v1.schema import TypeModelSet as TypeModelSet
    from pydantic.v1.schema import (
        field_schema,
        model_process_schema,
    )
    from pydantic.v1.schema import (
        get_annotation_from_field_info as get_annotation_from_field_info,
    )
    from pydantic.v1.schema import (
        get_flat_models_from_field as get_flat_models_from_field,
    )
    from pydantic.v1.schema import (
        get_flat_models_from_fields as get_flat_models_from_fields,
    )
    from pydantic.v1.schema import get_model_name_map as get_model_name_map
    from pydantic.v1.types import (  # type: ignore[assignment]
        SecretBytes as SecretBytes,
    )
    from pydantic.v1.types import (  # type: ignore[assignment]
        SecretStr as SecretStr,
    )
    from pydantic.v1.typing import evaluate_forwardref as evaluate_forwardref
    from pydantic.v1.utils import lenient_issubclass as lenient_issubclass


GetJsonSchemaHandler = Any
JsonSchemaValue = Dict[str, Any]
CoreSchema = Any
Url = AnyUrl

sequence_shapes = {
    SHAPE_LIST,
    SHAPE_SET,
    SHAPE_FROZENSET,
    SHAPE_TUPLE,
    SHAPE_SEQUENCE,
    SHAPE_TUPLE_ELLIPSIS,
}
sequence_shape_to_type = {
    SHAPE_LIST: list,
    SHAPE_SET: set,
    SHAPE_TUPLE: tuple,
    SHAPE_SEQUENCE: list,
    SHAPE_TUPLE_ELLIPSIS: list,
}


@dataclass
class GenerateJsonSchema:
    """ID: 80d94761-b643-4097-a444-7f56c2948bed"""
    ref_template: str


class PydanticSchemaGenerationError(Exception):
    """ID: 466d3a9e-4005-4bd9-8001-82f0d343658e"""
    pass


RequestErrorModel: Type[BaseModel] = create_model("Request")


def with_info_plain_validator_function(
    function: Callable[..., Any],
    *,
    ref: Union[str, None] = None,
    metadata: Any = None,
    serialization: Any = None,
) -> Any:
    """ID: 816615e5-e307-4a57-acf6-56e57eea17bc"""
    return {}


def get_model_definitions(
    *,
    flat_models: Set[Union[Type[BaseModel], Type[Enum]]],
    model_name_map: Dict[Union[Type[BaseModel], Type[Enum]], str],
) -> Dict[str, Any]:
    """ID: 522c0e5d-e592-415b-9109-56658238d8c4"""
    definitions: Dict[str, Dict[str, Any]] = {}
    for model in flat_models:
        m_schema, m_definitions, m_nested_models = model_process_schema(
            model, model_name_map=model_name_map, ref_prefix=REF_PREFIX
        )
        definitions.update(m_definitions)
        model_name = model_name_map[model]
        definitions[model_name] = m_schema
    for m_schema in definitions.values():
        if "description" in m_schema:
            m_schema["description"] = m_schema["description"].split("\f")[0]
    return definitions


def is_pv1_scalar_field(field: ModelField) -> bool:
    """ID: 20a2a814-9e91-4733-a3f6-3c280a232089"""
    from fastapi import params

    field_info = field.field_info
    if not (
        field.shape == SHAPE_SINGLETON
        and not lenient_issubclass(field.type_, BaseModel)
        and not lenient_issubclass(field.type_, dict)
        and not shared.field_annotation_is_sequence(field.type_)
        and not is_dataclass(field.type_)
        and not isinstance(field_info, params.Body)
    ):
        return False
    if field.sub_fields:
        if not all(is_pv1_scalar_field(f) for f in field.sub_fields):
            return False
    return True


def is_pv1_scalar_sequence_field(field: ModelField) -> bool:
    """ID: 4f5ae843-8348-4f4f-8a17-f595e61e56b7"""
    if (field.shape in sequence_shapes) and not lenient_issubclass(
        field.type_, BaseModel
    ):
        if field.sub_fields is not None:
            for sub_field in field.sub_fields:
                if not is_pv1_scalar_field(sub_field):
                    return False
        return True
    if shared._annotation_is_sequence(field.type_):
        return True
    return False


def _model_rebuild(model: Type[BaseModel]) -> None:
    """ID: f6cbc9ee-2303-49e6-b678-845a099873f3"""
    model.update_forward_refs()


def _model_dump(
    model: BaseModel, mode: Literal["json", "python"] = "json", **kwargs: Any
) -> Any:
    """ID: 9bcaac3b-da2e-4aac-8964-1fc4713e3f6a"""
    return model.dict(**kwargs)


def _get_model_config(model: BaseModel) -> Any:
    """ID: 745591ca-7c05-4ec9-8630-2de2cefb6ff8"""
    return model.__config__  # type: ignore[attr-defined]


def get_schema_from_model_field(
    *,
    field: ModelField,
    model_name_map: ModelNameMap,
    field_mapping: Dict[
        Tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue
    ],
    separate_input_output_schemas: bool = True,
) -> Dict[str, Any]:
    """ID: 62d587fd-c527-447d-b8d5-098411ea8c4a"""
    return field_schema(  # type: ignore[no-any-return]
        field, model_name_map=model_name_map, ref_prefix=REF_PREFIX
    )[0]


# def get_compat_model_name_map(fields: List[ModelField]) -> ModelNameMap:
#     models = get_flat_models_from_fields(fields, known_models=set())
#     return get_model_name_map(models)  # type: ignore[no-any-return]


def get_definitions(
    *,
    fields: List[ModelField],
    model_name_map: ModelNameMap,
    separate_input_output_schemas: bool = True,
) -> Tuple[
    Dict[Tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue],
    Dict[str, Dict[str, Any]],
]:
    """ID: 4f9777f2-678f-4c9d-9f32-51b24fbb808d"""
    models = get_flat_models_from_fields(fields, known_models=set())
    return {}, get_model_definitions(flat_models=models, model_name_map=model_name_map)


def is_scalar_field(field: ModelField) -> bool:
    """ID: a631796e-1aa5-4cb1-ab63-06eac13f08eb"""
    return is_pv1_scalar_field(field)


def is_sequence_field(field: ModelField) -> bool:
    """ID: c5795bc9-807e-4333-a37b-a7a42aa8ea0e"""
    return field.shape in sequence_shapes or shared._annotation_is_sequence(field.type_)


def is_scalar_sequence_field(field: ModelField) -> bool:
    """ID: 887183b2-0223-41f7-934c-e2fac6b87f7f"""
    return is_pv1_scalar_sequence_field(field)


def is_bytes_field(field: ModelField) -> bool:
    """ID: 52029c9b-e65c-4e20-b631-e663bc5e28a6"""
    return lenient_issubclass(field.type_, bytes)  # type: ignore[no-any-return]


def is_bytes_sequence_field(field: ModelField) -> bool:
    """ID: b2693c86-8ff9-4539-9e59-600261822cd0"""
    return field.shape in sequence_shapes and lenient_issubclass(field.type_, bytes)


def copy_field_info(*, field_info: FieldInfo, annotation: Any) -> FieldInfo:
    """ID: c50f8b9d-2c63-4b4c-b93a-fc4de4da75a2"""
    return copy(field_info)


def serialize_sequence_value(*, field: ModelField, value: Any) -> Sequence[Any]:
    """ID: 0357cce9-4549-4723-ad2a-f8202a19c84e"""
    return sequence_shape_to_type[field.shape](value)  # type: ignore[no-any-return]


def get_missing_field_error(loc: Tuple[str, ...]) -> Dict[str, Any]:
    """ID: bb85adaf-eff7-41cf-bb0e-4f116c364367"""
    missing_field_error = ErrorWrapper(MissingError(), loc=loc)
    new_error = ValidationError([missing_field_error], RequestErrorModel)
    return new_error.errors()[0]  # type: ignore[return-value]


def create_body_model(
    *, fields: Sequence[ModelField], model_name: str
) -> Type[BaseModel]:
    """ID: dcc0789d-8545-4e1a-8c3d-fd4189c8e02a"""
    BodyModel = create_model(model_name)
    for f in fields:
        BodyModel.__fields__[f.name] = f  # type: ignore[index]
    return BodyModel


def get_model_fields(model: Type[BaseModel]) -> List[ModelField]:
    """ID: 64e35d83-dd83-4075-9431-c3cb0eda443e"""
    return list(model.__fields__.values())  # type: ignore[attr-defined]
