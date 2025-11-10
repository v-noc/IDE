import warnings
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

from fastapi.openapi.models import Example
from pydantic.fields import FieldInfo
from typing_extensions import Annotated, deprecated

from ._compat import (
    PYDANTIC_V2,
    PYDANTIC_VERSION_MINOR_TUPLE,
    Undefined,
)

_Unset: Any = Undefined


class ParamTypes(Enum):
    """ID: e60da896-758e-4ea3-bb81-22302ce8d6c4"""
    query = "query"
    header = "header"
    path = "path"
    cookie = "cookie"


class Param(FieldInfo):  # type: ignore[misc]
    """ID: 9cfab1a7-b70f-4ec4-8c12-b1b8ec6df834"""
    in_: ParamTypes

    def __init__(
        self,
        default: Any = Undefined,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        annotation: Optional[Any] = None,
        alias: Optional[str] = None,
        alias_priority: Union[int, None] = _Unset,
        # TODO: update when deprecating Pydantic v1, import these types
        # validation_alias: str | AliasPath | AliasChoices | None
        validation_alias: Union[str, None] = None,
        serialization_alias: Union[str, None] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        regex: Annotated[
            Optional[str],
            deprecated(
                "Deprecated in FastAPI 0.100.0 and Pydantic v2, use `pattern` instead."
            ),
        ] = None,
        discriminator: Union[str, None] = None,
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
        example: Annotated[
            Optional[Any],
            deprecated(
                "Deprecated in OpenAPI 3.1.0 that now uses JSON Schema 2020-12, "
                "although still supported. Use examples instead."
            ),
        ] = _Unset,
        openapi_examples: Optional[Dict[str, Example]] = None,
        deprecated: Union[deprecated, str, bool, None] = None,
        include_in_schema: bool = True,
        json_schema_extra: Union[Dict[str, Any], None] = None,
        **extra: Any,
    ):
        """ID: 37f5e85f-b353-4365-9167-e0d0094fd7cd"""
        if example is not _Unset:
            warnings.warn(
                "`example` has been deprecated, please use `examples` instead",
                category=DeprecationWarning,
                stacklevel=4,
            )
        self.example = example
        self.include_in_schema = include_in_schema
        self.openapi_examples = openapi_examples
        kwargs = dict(
            default=default,
            default_factory=default_factory,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            discriminator=discriminator,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            **extra,
        )
        if examples is not None:
            kwargs["examples"] = examples
        if regex is not None:
            warnings.warn(
                "`regex` has been deprecated, please use `pattern` instead",
                category=DeprecationWarning,
                stacklevel=4,
            )
        current_json_schema_extra = json_schema_extra or extra
        if PYDANTIC_VERSION_MINOR_TUPLE < (2, 7):
            self.deprecated = deprecated
        else:
            kwargs["deprecated"] = deprecated
        if PYDANTIC_V2:
            kwargs.update(
                {
                    "annotation": annotation,
                    "alias_priority": alias_priority,
                    "validation_alias": validation_alias,
                    "serialization_alias": serialization_alias,
                    "strict": strict,
                    "json_schema_extra": current_json_schema_extra,
                }
            )
            kwargs["pattern"] = pattern or regex
        else:
            kwargs["regex"] = pattern or regex
            kwargs.update(**current_json_schema_extra)
        use_kwargs = {k: v for k, v in kwargs.items() if v is not _Unset}

        super().__init__(**use_kwargs)

    def __repr__(self) -> str:
        """ID: 16391bec-92a3-4ac9-833d-9c632a95555c"""
        return f"{self.__class__.__name__}({self.default})"


class Path(Param):  # type: ignore[misc]
    """ID: 63f6f29b-a16e-4f9f-97bc-407c7f072713"""
    in_ = ParamTypes.path

    def __init__(
        self,
        default: Any = ...,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        annotation: Optional[Any] = None,
        alias: Optional[str] = None,
        alias_priority: Union[int, None] = _Unset,
        # TODO: update when deprecating Pydantic v1, import these types
        # validation_alias: str | AliasPath | AliasChoices | None
        validation_alias: Union[str, None] = None,
        serialization_alias: Union[str, None] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        regex: Annotated[
            Optional[str],
            deprecated(
                "Deprecated in FastAPI 0.100.0 and Pydantic v2, use `pattern` instead."
            ),
        ] = None,
        discriminator: Union[str, None] = None,
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
        example: Annotated[
            Optional[Any],
            deprecated(
                "Deprecated in OpenAPI 3.1.0 that now uses JSON Schema 2020-12, "
                "although still supported. Use examples instead."
            ),
        ] = _Unset,
        openapi_examples: Optional[Dict[str, Example]] = None,
        deprecated: Union[deprecated, str, bool, None] = None,
        include_in_schema: bool = True,
        json_schema_extra: Union[Dict[str, Any], None] = None,
        **extra: Any,
    ):
        """ID: 13311d61-ea91-4367-ab00-0f18b5195abc"""
        assert default is ..., "Path parameters cannot have a default value"
        self.in_ = self.in_
        super().__init__(
            default=default,
            default_factory=default_factory,
            annotation=annotation,
            alias=alias,
            alias_priority=alias_priority,
            validation_alias=validation_alias,
            serialization_alias=serialization_alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            regex=regex,
            discriminator=discriminator,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            deprecated=deprecated,
            example=example,
            examples=examples,
            openapi_examples=openapi_examples,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


class Query(Param):  # type: ignore[misc]
    """ID: c92c1d67-9094-4c8e-8035-cb694cec65f5"""
    in_ = ParamTypes.query

    def __init__(
        self,
        default: Any = Undefined,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        annotation: Optional[Any] = None,
        alias: Optional[str] = None,
        alias_priority: Union[int, None] = _Unset,
        # TODO: update when deprecating Pydantic v1, import these types
        # validation_alias: str | AliasPath | AliasChoices | None
        validation_alias: Union[str, None] = None,
        serialization_alias: Union[str, None] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        regex: Annotated[
            Optional[str],
            deprecated(
                "Deprecated in FastAPI 0.100.0 and Pydantic v2, use `pattern` instead."
            ),
        ] = None,
        discriminator: Union[str, None] = None,
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
        example: Annotated[
            Optional[Any],
            deprecated(
                "Deprecated in OpenAPI 3.1.0 that now uses JSON Schema 2020-12, "
                "although still supported. Use examples instead."
            ),
        ] = _Unset,
        openapi_examples: Optional[Dict[str, Example]] = None,
        deprecated: Union[deprecated, str, bool, None] = None,
        include_in_schema: bool = True,
        json_schema_extra: Union[Dict[str, Any], None] = None,
        **extra: Any,
    ):
        """ID: f411e4f6-e440-42f1-94e7-d3be2cd2a471"""
        super().__init__(
            default=default,
            default_factory=default_factory,
            annotation=annotation,
            alias=alias,
            alias_priority=alias_priority,
            validation_alias=validation_alias,
            serialization_alias=serialization_alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            regex=regex,
            discriminator=discriminator,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            deprecated=deprecated,
            example=example,
            examples=examples,
            openapi_examples=openapi_examples,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


class Header(Param):  # type: ignore[misc]
    """ID: f8468a6f-b6b9-4b1c-80fa-f237186b7699"""
    in_ = ParamTypes.header

    def __init__(
        self,
        default: Any = Undefined,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        annotation: Optional[Any] = None,
        alias: Optional[str] = None,
        alias_priority: Union[int, None] = _Unset,
        # TODO: update when deprecating Pydantic v1, import these types
        # validation_alias: str | AliasPath | AliasChoices | None
        validation_alias: Union[str, None] = None,
        serialization_alias: Union[str, None] = None,
        convert_underscores: bool = True,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        regex: Annotated[
            Optional[str],
            deprecated(
                "Deprecated in FastAPI 0.100.0 and Pydantic v2, use `pattern` instead."
            ),
        ] = None,
        discriminator: Union[str, None] = None,
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
        example: Annotated[
            Optional[Any],
            deprecated(
                "Deprecated in OpenAPI 3.1.0 that now uses JSON Schema 2020-12, "
                "although still supported. Use examples instead."
            ),
        ] = _Unset,
        openapi_examples: Optional[Dict[str, Example]] = None,
        deprecated: Union[deprecated, str, bool, None] = None,
        include_in_schema: bool = True,
        json_schema_extra: Union[Dict[str, Any], None] = None,
        **extra: Any,
    ):
        """ID: 5c6c34c0-bdc0-4276-9a34-7e9334fe889d"""
        self.convert_underscores = convert_underscores
        super().__init__(
            default=default,
            default_factory=default_factory,
            annotation=annotation,
            alias=alias,
            alias_priority=alias_priority,
            validation_alias=validation_alias,
            serialization_alias=serialization_alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            regex=regex,
            discriminator=discriminator,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            deprecated=deprecated,
            example=example,
            examples=examples,
            openapi_examples=openapi_examples,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


class Cookie(Param):  # type: ignore[misc]
    """ID: 05e5cdbe-ba07-4f71-baa2-f0aead8adcf3"""
    in_ = ParamTypes.cookie

    def __init__(
        self,
        default: Any = Undefined,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        annotation: Optional[Any] = None,
        alias: Optional[str] = None,
        alias_priority: Union[int, None] = _Unset,
        # TODO: update when deprecating Pydantic v1, import these types
        # validation_alias: str | AliasPath | AliasChoices | None
        validation_alias: Union[str, None] = None,
        serialization_alias: Union[str, None] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        regex: Annotated[
            Optional[str],
            deprecated(
                "Deprecated in FastAPI 0.100.0 and Pydantic v2, use `pattern` instead."
            ),
        ] = None,
        discriminator: Union[str, None] = None,
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
        example: Annotated[
            Optional[Any],
            deprecated(
                "Deprecated in OpenAPI 3.1.0 that now uses JSON Schema 2020-12, "
                "although still supported. Use examples instead."
            ),
        ] = _Unset,
        openapi_examples: Optional[Dict[str, Example]] = None,
        deprecated: Union[deprecated, str, bool, None] = None,
        include_in_schema: bool = True,
        json_schema_extra: Union[Dict[str, Any], None] = None,
        **extra: Any,
    ):
        """ID: 3da0f4c7-7450-40e8-a04a-92ed5e0788bc"""
        super().__init__(
            default=default,
            default_factory=default_factory,
            annotation=annotation,
            alias=alias,
            alias_priority=alias_priority,
            validation_alias=validation_alias,
            serialization_alias=serialization_alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            regex=regex,
            discriminator=discriminator,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            deprecated=deprecated,
            example=example,
            examples=examples,
            openapi_examples=openapi_examples,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


class Body(FieldInfo):  # type: ignore[misc]
    """ID: 4698fd97-0166-47e0-9688-660c0b3a9338"""
    def __init__(
        self,
        default: Any = Undefined,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        annotation: Optional[Any] = None,
        embed: Union[bool, None] = None,
        media_type: str = "application/json",
        alias: Optional[str] = None,
        alias_priority: Union[int, None] = _Unset,
        # TODO: update when deprecating Pydantic v1, import these types
        # validation_alias: str | AliasPath | AliasChoices | None
        validation_alias: Union[str, None] = None,
        serialization_alias: Union[str, None] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        regex: Annotated[
            Optional[str],
            deprecated(
                "Deprecated in FastAPI 0.100.0 and Pydantic v2, use `pattern` instead."
            ),
        ] = None,
        discriminator: Union[str, None] = None,
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
        example: Annotated[
            Optional[Any],
            deprecated(
                "Deprecated in OpenAPI 3.1.0 that now uses JSON Schema 2020-12, "
                "although still supported. Use examples instead."
            ),
        ] = _Unset,
        openapi_examples: Optional[Dict[str, Example]] = None,
        deprecated: Union[deprecated, str, bool, None] = None,
        include_in_schema: bool = True,
        json_schema_extra: Union[Dict[str, Any], None] = None,
        **extra: Any,
    ):
        """ID: 6c82f219-c800-4e07-b09e-18308e16a81c"""
        self.embed = embed
        self.media_type = media_type
        if example is not _Unset:
            warnings.warn(
                "`example` has been deprecated, please use `examples` instead",
                category=DeprecationWarning,
                stacklevel=4,
            )
        self.example = example
        self.include_in_schema = include_in_schema
        self.openapi_examples = openapi_examples
        kwargs = dict(
            default=default,
            default_factory=default_factory,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            discriminator=discriminator,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            **extra,
        )
        if examples is not None:
            kwargs["examples"] = examples
        if regex is not None:
            warnings.warn(
                "`regex` has been deprecated, please use `pattern` instead",
                category=DeprecationWarning,
                stacklevel=4,
            )
        current_json_schema_extra = json_schema_extra or extra
        if PYDANTIC_VERSION_MINOR_TUPLE < (2, 7):
            self.deprecated = deprecated
        else:
            kwargs["deprecated"] = deprecated
        if PYDANTIC_V2:
            kwargs.update(
                {
                    "annotation": annotation,
                    "alias_priority": alias_priority,
                    "validation_alias": validation_alias,
                    "serialization_alias": serialization_alias,
                    "strict": strict,
                    "json_schema_extra": current_json_schema_extra,
                }
            )
            kwargs["pattern"] = pattern or regex
        else:
            kwargs["regex"] = pattern or regex
            kwargs.update(**current_json_schema_extra)

        use_kwargs = {k: v for k, v in kwargs.items() if v is not _Unset}

        super().__init__(**use_kwargs)

    def __repr__(self) -> str:
        """ID: f2d2452c-2493-4c4a-9770-5cd2a494ce3e"""
        return f"{self.__class__.__name__}({self.default})"


class Form(Body):  # type: ignore[misc]
    """ID: 4bceefa4-4c62-4bf6-8eaa-e693396aa548"""
    def __init__(
        self,
        default: Any = Undefined,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        annotation: Optional[Any] = None,
        media_type: str = "application/x-www-form-urlencoded",
        alias: Optional[str] = None,
        alias_priority: Union[int, None] = _Unset,
        # TODO: update when deprecating Pydantic v1, import these types
        # validation_alias: str | AliasPath | AliasChoices | None
        validation_alias: Union[str, None] = None,
        serialization_alias: Union[str, None] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        regex: Annotated[
            Optional[str],
            deprecated(
                "Deprecated in FastAPI 0.100.0 and Pydantic v2, use `pattern` instead."
            ),
        ] = None,
        discriminator: Union[str, None] = None,
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
        example: Annotated[
            Optional[Any],
            deprecated(
                "Deprecated in OpenAPI 3.1.0 that now uses JSON Schema 2020-12, "
                "although still supported. Use examples instead."
            ),
        ] = _Unset,
        openapi_examples: Optional[Dict[str, Example]] = None,
        deprecated: Union[deprecated, str, bool, None] = None,
        include_in_schema: bool = True,
        json_schema_extra: Union[Dict[str, Any], None] = None,
        **extra: Any,
    ):
        """ID: 21d6661b-c8d6-49dd-829e-c0718501a7ff"""
        super().__init__(
            default=default,
            default_factory=default_factory,
            annotation=annotation,
            media_type=media_type,
            alias=alias,
            alias_priority=alias_priority,
            validation_alias=validation_alias,
            serialization_alias=serialization_alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            regex=regex,
            discriminator=discriminator,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            deprecated=deprecated,
            example=example,
            examples=examples,
            openapi_examples=openapi_examples,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


class File(Form):  # type: ignore[misc]
    """ID: 7ad58a99-af4d-40b7-b391-cf66553cfe60"""
    def __init__(
        self,
        default: Any = Undefined,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        annotation: Optional[Any] = None,
        media_type: str = "multipart/form-data",
        alias: Optional[str] = None,
        alias_priority: Union[int, None] = _Unset,
        # TODO: update when deprecating Pydantic v1, import these types
        # validation_alias: str | AliasPath | AliasChoices | None
        validation_alias: Union[str, None] = None,
        serialization_alias: Union[str, None] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        regex: Annotated[
            Optional[str],
            deprecated(
                "Deprecated in FastAPI 0.100.0 and Pydantic v2, use `pattern` instead."
            ),
        ] = None,
        discriminator: Union[str, None] = None,
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
        example: Annotated[
            Optional[Any],
            deprecated(
                "Deprecated in OpenAPI 3.1.0 that now uses JSON Schema 2020-12, "
                "although still supported. Use examples instead."
            ),
        ] = _Unset,
        openapi_examples: Optional[Dict[str, Example]] = None,
        deprecated: Union[deprecated, str, bool, None] = None,
        include_in_schema: bool = True,
        json_schema_extra: Union[Dict[str, Any], None] = None,
        **extra: Any,
    ):
        """ID: 534a27f6-87d6-4f70-8923-ea9b1db9b8bf"""
        super().__init__(
            default=default,
            default_factory=default_factory,
            annotation=annotation,
            media_type=media_type,
            alias=alias,
            alias_priority=alias_priority,
            validation_alias=validation_alias,
            serialization_alias=serialization_alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            regex=regex,
            discriminator=discriminator,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            deprecated=deprecated,
            example=example,
            examples=examples,
            openapi_examples=openapi_examples,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


class Depends:
    """ID: ce51812f-e534-4520-bb85-30c2767960b9"""
    def __init__(
        self, dependency: Optional[Callable[..., Any]] = None, *, use_cache: bool = True
    ):
        """ID: e34d4be5-d1a3-473d-b2ca-7731c3a2d260"""
        self.dependency = dependency
        self.use_cache = use_cache

    def __repr__(self) -> str:
        """ID: 5eb74480-e256-44fd-a85d-22a980f87ece"""
        attr = getattr(self.dependency, "__name__", type(self.dependency).__name__)
        cache = "" if self.use_cache else ", use_cache=False"
        return f"{self.__class__.__name__}({attr}{cache})"


class Security(Depends):
    """ID: a237809b-93a0-4c1e-9c3e-d9095eb78c2b"""
    def __init__(
        self,
        dependency: Optional[Callable[..., Any]] = None,
        *,
        scopes: Optional[Sequence[str]] = None,
        use_cache: bool = True,
    ):
        """ID: 5a2a3122-4fa9-4425-9b9f-ce4f174e4f69"""
        super().__init__(dependency=dependency, use_cache=use_cache)
        self.scopes = scopes or []
