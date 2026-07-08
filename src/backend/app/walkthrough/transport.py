from __future__ import annotations

from collections.abc import AsyncIterator, Callable

import orjson
from fastapi.responses import StreamingResponse


def ndjson_response(
    frame_source: Callable[[], AsyncIterator[dict]],
) -> StreamingResponse:
    async def body() -> AsyncIterator[bytes]:
        async for frame in frame_source():
            yield orjson.dumps(frame) + b"\n"

    return StreamingResponse(body(), media_type="application/x-ndjson")
