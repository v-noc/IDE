
from arangoasync import ArangoClient
from arangoasync.auth import Auth
from arangoasync.database import AsyncDatabase

from ..config.settings import get_settings

# NOTE: python-arango-async uses an async context manager to initialize
# underlying resources. Returning a database handle from inside an `async with`
# block would immediately close the client and invalidate the handle.
_client: ArangoClient | None = None
_db: AsyncDatabase | None = None


async def get_db_async_client() -> AsyncDatabase:
    """Return a cached AsyncDatabase connection (python-arango-async)."""
    global _client, _db
    if _db is not None:
        return _db

    settings = get_settings()
    _client = ArangoClient(hosts=settings.ARANGO_HOST)
    # Manually enter the async context once and keep it alive for the process.
    await _client.__aenter__()

    auth = Auth(username=settings.ARANGO_USER,
                password=settings.ARANGO_PASSWORD)
    _db = await _client.db(settings.ARANGO_DB, auth=auth)
    return _db


async def get_db() -> AsyncDatabase:
    """
    FastAPI dependency: returns the process-wide cached AsyncDatabase.

    Kept as `get_db` for compatibility with existing imports.
    """
    return await get_db_async_client()


def close_db_client() -> None:
    """Close the global Arango client (best-effort)."""
    global _client, _db
    try:
        if _client is not None:
            _client.close()
    finally:
        _client = None
        _db = None
