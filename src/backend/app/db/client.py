"""
TerminusDB async client module.

Provides a singleton AsyncClient instance with proper lifecycle
management for use with FastAPI.
"""

from .async_terminus_client import AsyncClient
from ..config.settings import get_settings

_client: AsyncClient | None = None


async def _build_client() -> AsyncClient:
    settings = get_settings()
    client = AsyncClient(settings.TERMINUS_HOST)
    try:
        await client.connect(
            db=settings.TERMINUS_DB,
            user=settings.TERMINUS_USER,
            key=settings.TERMINUS_KEY,
            team=settings.TERMINUS_TEAM,
        )
    except Exception:
        await client.create_database(
            settings.TERMINUS_DB,
            label=settings.TERMINUS_DB,
            description="V-NOC code analysis graph",
        )
        await client.connect(
            db=settings.TERMINUS_DB,
            user=settings.TERMINUS_USER,
            key=settings.TERMINUS_KEY,
            team=settings.TERMINUS_TEAM,
        )
    return client


async def get_terminus_client() -> AsyncClient:
    global _client
    if _client is None:
        _client = await _build_client()
    return _client


async def get_db() -> AsyncClient:
    """FastAPI dependency — returns the async TerminusDB client."""
    return await get_terminus_client()


async def close_db_client() -> None:
    global _client
    try:
        if _client is not None:
            await _client.close()
    finally:
        _client = None
