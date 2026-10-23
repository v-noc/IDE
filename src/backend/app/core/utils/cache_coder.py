import orjson
from typing import Any
from fastapi_cache.coder import Coder


class OrjsonCoder(Coder):
    @classmethod
    def encode(cls, value: Any) -> bytes:
        return orjson.dumps(
            value,
            default=cls._default,
            option=orjson.OPT_SERIALIZE_NUMPY,
        )

    @classmethod
    def decode(cls, value: bytes) -> Any:
        return orjson.loads(value)

    @classmethod
    def _default(cls, obj: Any) -> Any:
        if hasattr(obj, "model_dump"):
            return obj.model_dump(mode="json")
        if isinstance(obj, (set, frozenset)):
            return list(obj)
        raise TypeError(f"Type not serializable: {type(obj)}")
