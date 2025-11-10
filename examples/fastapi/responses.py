from typing import Any

from starlette.responses import FileResponse as FileResponse  # noqa
from starlette.responses import HTMLResponse as HTMLResponse  # noqa
from starlette.responses import JSONResponse as JSONResponse  # noqa
from starlette.responses import PlainTextResponse as PlainTextResponse  # noqa
from starlette.responses import RedirectResponse as RedirectResponse  # noqa
from starlette.responses import Response as Response  # noqa
from starlette.responses import StreamingResponse as StreamingResponse  # noqa

try:
    import ujson
except ImportError:  # pragma: nocover
    ujson = None  # type: ignore


try:
    import orjson
except ImportError:  # pragma: nocover
    orjson = None  # type: ignore


class UJSONResponse(JSONResponse):
    """JSON response using the high-performance ujson library to serialize data to JSON.

Read more about it in the
[FastAPI docs for Custom Response - HTML, Stream, File, others](https://fastapi.tiangolo.com/advanced/custom-response/).

ID: c64b1c9a-5690-4943-8405-3b7defb95314"""

    def render(self, content: Any) -> bytes:
        """ID: faf3d01f-12c9-470c-89c6-3cd38ddf052f"""
        assert ujson is not None, "ujson must be installed to use UJSONResponse"
        return ujson.dumps(content, ensure_ascii=False).encode("utf-8")


class ORJSONResponse(JSONResponse):
    """JSON response using the high-performance orjson library to serialize data to JSON.

Read more about it in the
[FastAPI docs for Custom Response - HTML, Stream, File, others](https://fastapi.tiangolo.com/advanced/custom-response/).

ID: cd950eab-b388-402d-9aa5-d081786f6ed0"""

    def render(self, content: Any) -> bytes:
        """ID: 445ca0ec-cb1c-48b6-a37f-21ac3ee172a5"""
        assert orjson is not None, "orjson must be installed to use ORJSONResponse"
        return orjson.dumps(
            content, option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY
        )
