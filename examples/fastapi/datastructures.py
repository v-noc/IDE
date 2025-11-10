from typing import (
    Any,
    BinaryIO,
    Callable,
    Dict,
    Iterable,
    Optional,
    Type,
    TypeVar,
    cast,
)

from annotated_doc import Doc
from fastapi._compat import (
    CoreSchema,
    GetJsonSchemaHandler,
    JsonSchemaValue,
)
from starlette.datastructures import URL as URL  # noqa: F401
from starlette.datastructures import Address as Address  # noqa: F401
from starlette.datastructures import FormData as FormData  # noqa: F401
from starlette.datastructures import Headers as Headers  # noqa: F401
from starlette.datastructures import QueryParams as QueryParams  # noqa: F401
from starlette.datastructures import State as State  # noqa: F401
from starlette.datastructures import UploadFile as StarletteUploadFile
from typing_extensions import Annotated


class UploadFile(StarletteUploadFile):
    """A file uploaded in a request.

Define it as a *path operation function* (or dependency) parameter.

If you are using a regular `def` function, you can use the `upload_file.file`
attribute to access the raw standard Python file (blocking, not async), useful and
needed for non-async code.

Read more about it in the
[FastAPI docs for Request Files](https://fastapi.tiangolo.com/tutorial/request-files/).

## Example

```python
from typing import Annotated

from fastapi import FastAPI, File, UploadFile

app = FastAPI()


@app.post("/files/")
async def create_file(file: Annotated[bytes, File()]):
    return {"file_size": len(file)}


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    return {"filename": file.filename}
```

ID: 4eb67954-2be6-4b91-b312-201aa80363de"""

    file: Annotated[
        BinaryIO,
        Doc("The standard Python file object (non-async)."),
    ]
    filename: Annotated[Optional[str], Doc("The original file name.")]
    size: Annotated[Optional[int], Doc("The size of the file in bytes.")]
    headers: Annotated[Headers, Doc("The headers of the request.")]
    content_type: Annotated[
        Optional[str], Doc("The content type of the request, from the headers.")
    ]

    async def write(
        self,
        data: Annotated[
            bytes,
            Doc(
                """
                The bytes to write to the file.
                """
            ),
        ],
    ) -> None:
        """Write some bytes to the file.

You normally wouldn't use this from a file you read in a request.

To be awaitable, compatible with async, this is run in threadpool.

ID: fd667ae4-71d4-4672-ae3c-fe35814b7561"""
        return await super().write(data)

    async def read(
        self,
        size: Annotated[
            int,
            Doc(
                """
                The number of bytes to read from the file.
                """
            ),
        ] = -1,
    ) -> bytes:
        """Read some bytes from the file.

To be awaitable, compatible with async, this is run in threadpool.

ID: 64b49202-212e-4c5f-9e31-6866256a7315"""
        return await super().read(size)

    async def seek(
        self,
        offset: Annotated[
            int,
            Doc(
                """
                The position in bytes to seek to in the file.
                """
            ),
        ],
    ) -> None:
        """Move to a position in the file.

Any next read or write will be done from that position.

To be awaitable, compatible with async, this is run in threadpool.

ID: 5016486c-4beb-489c-beef-2e335810c2fd"""
        return await super().seek(offset)

    async def close(self) -> None:
        """Close the file.

To be awaitable, compatible with async, this is run in threadpool.

ID: 0f08b356-dc39-450b-bca4-08f63b471c3a"""
        return await super().close()

    @classmethod
    def __get_validators__(cls: Type["UploadFile"]) -> Iterable[Callable[..., Any]]:
        """ID: 029c95ee-2f42-4124-9dad-63724acb1719"""
        yield cls.validate

    @classmethod
    def validate(cls: Type["UploadFile"], v: Any) -> Any:
        """ID: e000b394-0a3b-4da9-b678-5ab52b37c39b"""
        if not isinstance(v, StarletteUploadFile):
            raise ValueError(f"Expected UploadFile, received: {type(v)}")
        return v

    @classmethod
    def _validate(cls, __input_value: Any, _: Any) -> "UploadFile":
        """ID: b70c864c-0647-44cd-b567-a1baac9ce21a"""
        if not isinstance(__input_value, StarletteUploadFile):
            raise ValueError(f"Expected UploadFile, received: {type(__input_value)}")
        return cast(UploadFile, __input_value)

    # TODO: remove when deprecating Pydantic v1
    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        """ID: e46d779f-a2b3-4fc1-9180-50e4c828593a"""
        field_schema.update({"type": "string", "format": "binary"})

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """ID: 694dcae5-1d82-402f-90fb-e2765585bc54"""
        return {"type": "string", "format": "binary"}

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Type[Any], handler: Callable[[Any], CoreSchema]
    ) -> CoreSchema:
        """ID: 0844ca20-1d08-4cfc-9a1d-5bc251b10b91"""
        from ._compat.v2 import with_info_plain_validator_function

        return with_info_plain_validator_function(cls._validate)


class DefaultPlaceholder:
    """You shouldn't use this class directly.

It's used internally to recognize when a default value has been overwritten, even
if the overridden default value was truthy.

ID: f9514c56-6a20-4564-9f4b-aacbe77665ab"""

    def __init__(self, value: Any):
        """ID: 81a40305-bcef-48f5-8a94-8852f0e461fd"""
        self.value = value

    def __bool__(self) -> bool:
        """ID: 0c8f519f-e82f-414a-87d3-dc7c3204e9e3"""
        return bool(self.value)

    def __eq__(self, o: object) -> bool:
        """ID: d5d3e04a-528a-4cff-8072-e3e29d58d0f8"""
        return isinstance(o, DefaultPlaceholder) and o.value == self.value


DefaultType = TypeVar("DefaultType")


def Default(value: DefaultType) -> DefaultType:
    """You shouldn't use this function directly.

It's used internally to recognize when a default value has been overwritten, even
if the overridden default value was truthy.

ID: 26fb5190-4b8d-43ae-ad57-a30606a6cb80"""
    return DefaultPlaceholder(value)  # type: ignore
