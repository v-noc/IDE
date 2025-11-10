from typing import Optional

from annotated_doc import Doc
from fastapi.openapi.models import APIKey, APIKeyIn
from fastapi.security.base import SecurityBase
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.status import HTTP_403_FORBIDDEN
from typing_extensions import Annotated


class APIKeyBase(SecurityBase):
    """ID: a6076905-28d9-4709-b88f-fd937513951d"""
    @staticmethod
    def check_api_key(api_key: Optional[str], auto_error: bool) -> Optional[str]:
        """ID: e74761bf-fdd3-41cc-8a2b-511c91698bce"""
        if not api_key:
            if auto_error:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
                )
            return None
        return api_key


class APIKeyQuery(APIKeyBase):
    """API key authentication using a query parameter.

This defines the name of the query parameter that should be provided in the request
with the API key and integrates that into the OpenAPI documentation. It extracts
the key value sent in the query parameter automatically and provides it as the
dependency result. But it doesn't define how to send that API key to the client.

## Usage

Create an instance object and use that object as the dependency in `Depends()`.

The dependency result will be a string containing the key value.

## Example

```python
from fastapi import Depends, FastAPI
from fastapi.security import APIKeyQuery

app = FastAPI()

query_scheme = APIKeyQuery(name="api_key")


@app.get("/items/")
async def read_items(api_key: str = Depends(query_scheme)):
    return {"api_key": api_key}
```

ID: 3064c4dc-a628-4098-837c-7512bc4308ff"""

    def __init__(
        self,
        *,
        name: Annotated[
            str,
            Doc("Query parameter name."),
        ],
        scheme_name: Annotated[
            Optional[str],
            Doc(
                """
                Security scheme name.

                It will be included in the generated OpenAPI (e.g. visible at `/docs`).
                """
            ),
        ] = None,
        description: Annotated[
            Optional[str],
            Doc(
                """
                Security scheme description.

                It will be included in the generated OpenAPI (e.g. visible at `/docs`).
                """
            ),
        ] = None,
        auto_error: Annotated[
            bool,
            Doc(
                """
                By default, if the query parameter is not provided, `APIKeyQuery` will
                automatically cancel the request and send the client an error.

                If `auto_error` is set to `False`, when the query parameter is not
                available, instead of erroring out, the dependency result will be
                `None`.

                This is useful when you want to have optional authentication.

                It is also useful when you want to have authentication that can be
                provided in one of multiple optional ways (for example, in a query
                parameter or in an HTTP Bearer token).
                """
            ),
        ] = True,
    ):
        """ID: 6ca07914-fd65-471a-857c-8503d65db959"""
        self.model: APIKey = APIKey(
            **{"in": APIKeyIn.query},
            name=name,
            description=description,
        )
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error

    async def __call__(self, request: Request) -> Optional[str]:
        """ID: e25cc62c-308e-440a-a05c-95314b0ee07c"""
        api_key = request.query_params.get(self.model.name)
        return self.check_api_key(api_key, self.auto_error)


class APIKeyHeader(APIKeyBase):
    """API key authentication using a header.

This defines the name of the header that should be provided in the request with
the API key and integrates that into the OpenAPI documentation. It extracts
the key value sent in the header automatically and provides it as the dependency
result. But it doesn't define how to send that key to the client.

## Usage

Create an instance object and use that object as the dependency in `Depends()`.

The dependency result will be a string containing the key value.

## Example

```python
from fastapi import Depends, FastAPI
from fastapi.security import APIKeyHeader

app = FastAPI()

header_scheme = APIKeyHeader(name="x-key")


@app.get("/items/")
async def read_items(key: str = Depends(header_scheme)):
    return {"key": key}
```

ID: 956b6dc8-9924-470a-b207-f0c7bb5a330b"""

    def __init__(
        self,
        *,
        name: Annotated[str, Doc("Header name.")],
        scheme_name: Annotated[
            Optional[str],
            Doc(
                """
                Security scheme name.

                It will be included in the generated OpenAPI (e.g. visible at `/docs`).
                """
            ),
        ] = None,
        description: Annotated[
            Optional[str],
            Doc(
                """
                Security scheme description.

                It will be included in the generated OpenAPI (e.g. visible at `/docs`).
                """
            ),
        ] = None,
        auto_error: Annotated[
            bool,
            Doc(
                """
                By default, if the header is not provided, `APIKeyHeader` will
                automatically cancel the request and send the client an error.

                If `auto_error` is set to `False`, when the header is not available,
                instead of erroring out, the dependency result will be `None`.

                This is useful when you want to have optional authentication.

                It is also useful when you want to have authentication that can be
                provided in one of multiple optional ways (for example, in a header or
                in an HTTP Bearer token).
                """
            ),
        ] = True,
    ):
        """ID: 79834043-e3ed-4415-8e0d-8e0d92cacc10"""
        self.model: APIKey = APIKey(
            **{"in": APIKeyIn.header},
            name=name,
            description=description,
        )
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error

    async def __call__(self, request: Request) -> Optional[str]:
        """ID: d466acab-6995-47ff-915e-e40cbccdcb16"""
        api_key = request.headers.get(self.model.name)
        return self.check_api_key(api_key, self.auto_error)


class APIKeyCookie(APIKeyBase):
    """API key authentication using a cookie.

This defines the name of the cookie that should be provided in the request with
the API key and integrates that into the OpenAPI documentation. It extracts
the key value sent in the cookie automatically and provides it as the dependency
result. But it doesn't define how to set that cookie.

## Usage

Create an instance object and use that object as the dependency in `Depends()`.

The dependency result will be a string containing the key value.

## Example

```python
from fastapi import Depends, FastAPI
from fastapi.security import APIKeyCookie

app = FastAPI()

cookie_scheme = APIKeyCookie(name="session")


@app.get("/items/")
async def read_items(session: str = Depends(cookie_scheme)):
    return {"session": session}
```

ID: a7211ee3-f526-44b9-b916-0d940fca4a0a"""

    def __init__(
        self,
        *,
        name: Annotated[str, Doc("Cookie name.")],
        scheme_name: Annotated[
            Optional[str],
            Doc(
                """
                Security scheme name.

                It will be included in the generated OpenAPI (e.g. visible at `/docs`).
                """
            ),
        ] = None,
        description: Annotated[
            Optional[str],
            Doc(
                """
                Security scheme description.

                It will be included in the generated OpenAPI (e.g. visible at `/docs`).
                """
            ),
        ] = None,
        auto_error: Annotated[
            bool,
            Doc(
                """
                By default, if the cookie is not provided, `APIKeyCookie` will
                automatically cancel the request and send the client an error.

                If `auto_error` is set to `False`, when the cookie is not available,
                instead of erroring out, the dependency result will be `None`.

                This is useful when you want to have optional authentication.

                It is also useful when you want to have authentication that can be
                provided in one of multiple optional ways (for example, in a cookie or
                in an HTTP Bearer token).
                """
            ),
        ] = True,
    ):
        """ID: de067899-1080-4fe3-8684-0fe2986da1e2"""
        self.model: APIKey = APIKey(
            **{"in": APIKeyIn.cookie},
            name=name,
            description=description,
        )
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error

    async def __call__(self, request: Request) -> Optional[str]:
        """ID: a47167d1-79d3-4a30-a5c4-f5f28f813526"""
        api_key = request.cookies.get(self.model.name)
        return self.check_api_key(api_key, self.auto_error)
