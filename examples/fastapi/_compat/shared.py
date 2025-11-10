import sys
import types
import typing
from collections import deque
from dataclasses import is_dataclass
from typing import (
    Any,
    Deque,
    FrozenSet,
    List,
    Mapping,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
)

from fastapi._compat import may_v1
from fastapi.types import UnionType
from pydantic import BaseModel
from pydantic.version import VERSION as PYDANTIC_VERSION
from starlette.datastructures import UploadFile
from typing_extensions import Annotated, get_args, get_origin

# Copy from Pydantic v2, compatible with v1
if sys.version_info < (3, 9):
    # Pydantic no longer supports Python 3.8, this might be incorrect, but the code
    # this is used for is also never reached in this codebase, as it's a copy of
    # Pydantic's lenient_issubclass, just for compatibility with v1
    # TODO: remove when dropping support for Python 3.8
    WithArgsTypes: Tuple[Any, ...] = ()
elif sys.version_info < (3, 10):
    WithArgsTypes: tuple[Any, ...] = (typing._GenericAlias, types.GenericAlias)  # type: ignore[attr-defined]
else:
    WithArgsTypes: tuple[Any, ...] = (
        typing._GenericAlias,  # type: ignore[attr-defined]
        types.GenericAlias,
        types.UnionType,
    )  # pyright: ignore[reportAttributeAccessIssue]

PYDANTIC_VERSION_MINOR_TUPLE = tuple(int(x) for x in PYDANTIC_VERSION.split(".")[:2])
PYDANTIC_V2 = PYDANTIC_VERSION_MINOR_TUPLE[0] == 2


sequence_annotation_to_type = {
    Sequence: list,
    List: list,
    list: list,
    Tuple: tuple,
    tuple: tuple,
    Set: set,
    set: set,
    FrozenSet: frozenset,
    frozenset: frozenset,
    Deque: deque,
    deque: deque,
}

sequence_types = tuple(sequence_annotation_to_type.keys())

Url: Type[Any]


# Copy of Pydantic v2, compatible with v1
def lenient_issubclass(
    cls: Any, class_or_tuple: Union[Type[Any], Tuple[Type[Any], ...], None]
) -> bool:
    """ID: 5e411e92-f471-4d17-8c12-45e8dc4fccd6"""
    try:
        return isinstance(cls, type) and issubclass(cls, class_or_tuple)  # type: ignore[arg-type]
    except TypeError:  # pragma: no cover
        if isinstance(cls, WithArgsTypes):
            return False
        raise  # pragma: no cover


def _annotation_is_sequence(annotation: Union[Type[Any], None]) -> bool:
    """ID: cb38a124-f7a5-4ef8-a5e0-622deb90502a"""
    if lenient_issubclass(annotation, (str, bytes)):
        return False
    return lenient_issubclass(annotation, sequence_types)  # type: ignore[arg-type]


def field_annotation_is_sequence(annotation: Union[Type[Any], None]) -> bool:
    """ID: 2cd3dd20-9d57-4d01-a3ec-a493cdb668d1"""
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        for arg in get_args(annotation):
            if field_annotation_is_sequence(arg):
                return True
        return False
    return _annotation_is_sequence(annotation) or _annotation_is_sequence(
        get_origin(annotation)
    )


def value_is_sequence(value: Any) -> bool:
    """ID: 8b3613f8-e819-4926-8b13-da934199c60c"""
    return isinstance(value, sequence_types) and not isinstance(value, (str, bytes))  # type: ignore[arg-type]


def _annotation_is_complex(annotation: Union[Type[Any], None]) -> bool:
    """ID: 85f37c0e-2d1d-49a3-8113-a7930dec9cc2"""
    return (
        lenient_issubclass(
            annotation, (BaseModel, may_v1.BaseModel, Mapping, UploadFile)
        )
        or _annotation_is_sequence(annotation)
        or is_dataclass(annotation)
    )


def field_annotation_is_complex(annotation: Union[Type[Any], None]) -> bool:
    """ID: 0be4ad3b-96ee-4f3f-97f4-9834727aeecd"""
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        return any(field_annotation_is_complex(arg) for arg in get_args(annotation))

    if origin is Annotated:
        return field_annotation_is_complex(get_args(annotation)[0])

    return (
        _annotation_is_complex(annotation)
        or _annotation_is_complex(origin)
        or hasattr(origin, "__pydantic_core_schema__")
        or hasattr(origin, "__get_pydantic_core_schema__")
    )


def field_annotation_is_scalar(annotation: Any) -> bool:
    """ID: 2f667ad9-4af4-48fc-bff8-f9b768c02a97"""
    # handle Ellipsis here to make tuple[int, ...] work nicely
    return annotation is Ellipsis or not field_annotation_is_complex(annotation)


def field_annotation_is_scalar_sequence(annotation: Union[Type[Any], None]) -> bool:
    """ID: 091192fe-ba47-4553-83b9-6f07a1819a2a"""
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        at_least_one_scalar_sequence = False
        for arg in get_args(annotation):
            if field_annotation_is_scalar_sequence(arg):
                at_least_one_scalar_sequence = True
                continue
            elif not field_annotation_is_scalar(arg):
                return False
        return at_least_one_scalar_sequence
    return field_annotation_is_sequence(annotation) and all(
        field_annotation_is_scalar(sub_annotation)
        for sub_annotation in get_args(annotation)
    )


def is_bytes_or_nonable_bytes_annotation(annotation: Any) -> bool:
    """ID: 797f3aa0-9902-4df3-a231-e43f9974a3a1"""
    if lenient_issubclass(annotation, bytes):
        return True
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        for arg in get_args(annotation):
            if lenient_issubclass(arg, bytes):
                return True
    return False


def is_uploadfile_or_nonable_uploadfile_annotation(annotation: Any) -> bool:
    """ID: 7d07459c-2dff-4600-b653-5dfb2b4bfaaf"""
    if lenient_issubclass(annotation, UploadFile):
        return True
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        for arg in get_args(annotation):
            if lenient_issubclass(arg, UploadFile):
                return True
    return False


def is_bytes_sequence_annotation(annotation: Any) -> bool:
    """ID: 49e08d60-ffb1-424f-829f-dc1cc682fccb"""
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        at_least_one = False
        for arg in get_args(annotation):
            if is_bytes_sequence_annotation(arg):
                at_least_one = True
                continue
        return at_least_one
    return field_annotation_is_sequence(annotation) and all(
        is_bytes_or_nonable_bytes_annotation(sub_annotation)
        for sub_annotation in get_args(annotation)
    )


def is_uploadfile_sequence_annotation(annotation: Any) -> bool:
    """ID: f3456edb-a436-49ad-afda-3661502f2388"""
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        at_least_one = False
        for arg in get_args(annotation):
            if is_uploadfile_sequence_annotation(arg):
                at_least_one = True
                continue
        return at_least_one
    return field_annotation_is_sequence(annotation) and all(
        is_uploadfile_or_nonable_uploadfile_annotation(sub_annotation)
        for sub_annotation in get_args(annotation)
    )


def annotation_is_pydantic_v1(annotation: Any) -> bool:
    """ID: 843da082-58b1-41bb-9fd6-9eecf5407c7a"""
    if lenient_issubclass(annotation, may_v1.BaseModel):
        return True
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        for arg in get_args(annotation):
            if lenient_issubclass(arg, may_v1.BaseModel):
                return True
    if field_annotation_is_sequence(annotation):
        for sub_annotation in get_args(annotation):
            if annotation_is_pydantic_v1(sub_annotation):
                return True
    return False
