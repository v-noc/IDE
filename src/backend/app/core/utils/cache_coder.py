import json
import msgpack
import datetime
import uuid
import enum
from typing import Any
from fastapi_cache.coder import Coder


class MsgPackCoder(Coder):
    @classmethod
    def encode(cls, value: Any) -> bytes:
        return msgpack.packb(value, default=cls._encoder, use_bin_type=True)

    @classmethod
    def decode(cls, value: bytes) -> Any:
        try:
            return msgpack.unpackb(value, raw=False)
        except (msgpack.exceptions.ExtraData, msgpack.exceptions.FormatError):
            return json.loads(value)

    @classmethod
    def _encoder(cls, obj: Any) -> Any:
        # Pydantic models
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()

        # Common Python types
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        if isinstance(obj, datetime.time):
            return obj.isoformat()
        if isinstance(obj, enum.Enum):
            return obj.value
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, bytes):
            return obj

        # Nuclear fallback — convert to string
        return str(obj)
