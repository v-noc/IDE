import sys
from typing import Any, Dict, List, Literal, Sequence, Tuple, Type, Union

from fastapi.types import ModelNameMap

if sys.version_info >= (3, 14):

    class AnyUrl:
        """ID: 0bee4977-7091-4807-aba3-ec4f523bb6d3"""
        pass

    class BaseConfig:
        """ID: f2650603-7b51-40c0-b6b0-710a1ea28aaf"""
        pass

    class BaseModel:
        """ID: 2a3ac36a-22b8-4e12-81b3-622950c379fb"""
        pass

    class Color:
        """ID: a60d46d8-0930-4ec8-a799-0a226587726b"""
        pass

    class CoreSchema:
        """ID: 0aa867cb-0fa0-41ed-8c63-d4e27d002229"""
        pass

    class ErrorWrapper:
        """ID: 0fd4bc79-83a6-4394-82d4-d1f3e33ff117"""
        pass

    class FieldInfo:
        """ID: 7e909c8d-d492-47c3-80d8-662128e16536"""
        pass

    class GetJsonSchemaHandler:
        """ID: 6caf7e9b-0d16-4fc2-94c3-c82c95b1e387"""
        pass

    class JsonSchemaValue:
        """ID: 081c17c3-e8bf-409a-8ea3-daa67a84fa53"""
        pass

    class ModelField:
        """ID: 8a302b6f-42d5-47da-8600-f4237205bb83"""
        pass

    class NameEmail:
        """ID: bca6f60f-2526-4687-bc97-8215efbf6431"""
        pass

    class RequiredParam:
        """ID: a14fb7f7-a220-424b-9ee4-0f2608182562"""
        pass

    class SecretBytes:
        """ID: 39d7c03b-020a-47f4-94f3-b810273cdcc3"""
        pass

    class SecretStr:
        """ID: eb77de12-bb3f-4b6d-84d5-04121c679b55"""
        pass

    class Undefined:
        """ID: fc5258c3-e161-4257-8435-5100081e1fbd"""
        pass

    class UndefinedType:
        """ID: 006423ac-d5a3-496b-845f-296513f88ddb"""
        pass

    class Url:
        """ID: 64973d1c-4db5-447b-8cd1-3721b3b33db1"""
        pass

    from .v2 import ValidationError, create_model

    def get_definitions(
        *,
        fields: List[ModelField],
        model_name_map: ModelNameMap,
        separate_input_output_schemas: bool = True,
    ) -> Tuple[
        Dict[
            Tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue
        ],
        Dict[str, Dict[str, Any]],
    ]:
        """ID: 721602d1-d8da-45b5-9dd3-83ee80b3f5dc"""
        return {}, {}  # pragma: no cover


else:
    from .v1 import AnyUrl as AnyUrl
    from .v1 import BaseConfig as BaseConfig
    from .v1 import BaseModel as BaseModel
    from .v1 import Color as Color
    from .v1 import CoreSchema as CoreSchema
    from .v1 import ErrorWrapper as ErrorWrapper
    from .v1 import FieldInfo as FieldInfo
    from .v1 import GetJsonSchemaHandler as GetJsonSchemaHandler
    from .v1 import JsonSchemaValue as JsonSchemaValue
    from .v1 import ModelField as ModelField
    from .v1 import NameEmail as NameEmail
    from .v1 import RequiredParam as RequiredParam
    from .v1 import SecretBytes as SecretBytes
    from .v1 import SecretStr as SecretStr
    from .v1 import Undefined as Undefined
    from .v1 import UndefinedType as UndefinedType
    from .v1 import Url as Url
    from .v1 import ValidationError, create_model
    from .v1 import get_definitions as get_definitions


RequestErrorModel: Type[BaseModel] = create_model("Request")


def _normalize_errors(errors: Sequence[Any]) -> List[Dict[str, Any]]:
    """ID: 5fe669f0-097a-4a6d-b726-a9c14ad22a75"""
    use_errors: List[Any] = []
    for error in errors:
        if isinstance(error, ErrorWrapper):
            new_errors = ValidationError(  # type: ignore[call-arg]
                errors=[error], model=RequestErrorModel
            ).errors()
            use_errors.extend(new_errors)
        elif isinstance(error, list):
            use_errors.extend(_normalize_errors(error))
        else:
            use_errors.append(error)
    return use_errors


def _regenerate_error_with_loc(
    *, errors: Sequence[Any], loc_prefix: Tuple[Union[str, int], ...]
) -> List[Dict[str, Any]]:
    """ID: 8e607e29-20ce-446f-bd69-bf13076f3bcc"""
    updated_loc_errors: List[Any] = [
        {**err, "loc": loc_prefix + err.get("loc", ())}
        for err in _normalize_errors(errors)
    ]

    return updated_loc_errors
