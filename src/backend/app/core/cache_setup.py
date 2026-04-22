"""fastapi-cache2: Redis or no-op backend; request-based keys (no Depends in key hash)."""
from __future__ import annotations

import hashlib
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any, Optional, Tuple

from fastapi import Request, Response
from fastapi_cache import FastAPICache
from fastapi_cache.types import Backend
from redis import asyncio as aioredis
from starlette.datastructures import URL

from app.config.settings import get_settings

# fastapi_cache `expire` is in seconds; one day.
DEFAULT_TTL = 24 * 60 * 60


def request_key_builder(
    func: Callable[..., Awaitable[Any]],
    namespace: str = "",
    *,
    request: Optional[Request] = None,
    response: Optional[Response] = None,
    args: tuple[Any, ...] = (),
    kwargs: Optional[MutableMapping[str, Any]] = None,
) -> str:
    """Key from handler identity + full URL (query) + V-NOC view headers (avoids injected deps)."""
    if request is not None:
        url: URL = request.url
        branch = request.headers.get("x-vnoc-branch", "main")
        ref = request.query_params.get("ref", "")
        compare_to = request.query_params.get("compare_to", "")
        material = (
            f"{func.__module__}:{func.__qualname__}:"
            f"{url.path}?{url.query}:"
            f"branch={branch}:ref={ref}:compare_to={compare_to}"
        )
        digest = hashlib.md5(material.encode("utf-8"), usedforsecurity=False).hexdigest()  # noqa: S324
        return f"{namespace}:{digest}"
    from fastapi_cache import default_key_builder  # local import: circular

    return default_key_builder(
        func, namespace, request=request, response=response, args=args, kwargs=dict(kwargs or {})
    )


class NoOpBackend(Backend):
    """Always miss; for ENABLE_CACHE=false or tests without Redis."""

    async def get_with_ttl(self, key: str) -> Tuple[int, Optional[bytes]]:
        return 0, None

    async def get(self, key: str) -> Optional[bytes]:
        return None

    async def set(
        self, key: str, value: bytes, expire: Optional[int] = None
    ) -> None:
        return None

    async def clear(self, namespace: Optional[str] = None, key: Optional[str] = None) -> int:
        return 0


async def init_cache(app) -> None:
    settings = get_settings()
    prefix = settings.CACHE_PREFIX
    if settings.ENABLE_CACHE:
        if not settings.REDIS_URL:
            raise ValueError("ENABLE_CACHE is true but REDIS_URL is not set")
        redis = aioredis.from_url(settings.REDIS_URL)
        app.state.redis = redis
        from fastapi_cache.backends.redis import RedisBackend

        FastAPICache.init(
            RedisBackend(redis),
            prefix=prefix,
            key_builder=request_key_builder,
        )
    else:
        app.state.redis = None
        FastAPICache.init(
            NoOpBackend(),
            prefix=prefix,
            key_builder=request_key_builder,
        )


async def shutdown_cache(app) -> None:
    redis = getattr(app.state, "redis", None)
    if redis is not None:
        await redis.aclose()
        app.state.redis = None
