import msgpack
from typing import Any
from fastapi_cache.coder import Coder


def _pydantic_encoder(obj: Any) -> Any:
    """Convert Pydantic models to dicts for msgpack."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    raise TypeError(f"Unknown type: {type(obj)}")


class MsgPackCoder(Coder):
    @classmethod
    def encode(cls, value: Any) -> bytes:
        return msgpack.packb(value, default=_pydantic_encoder, use_bin_type=True)

    @classmethod
    def decode(cls, value: bytes) -> Any:
        return msgpack.unpackb(value, raw=False)
