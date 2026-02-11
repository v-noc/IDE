"""
TerminusDB client module.

Provides a singleton Client instance that is shared across the application.
The TerminusDB Python client is synchronous, so we wrap calls for
compatibility with our async FastAPI stack.
"""

from terminusdb_client import Client
from ..config.settings import get_settings

# ---------- Singleton state ----------
_client: Client | None = None


def _build_client() -> Client:
    """
    Create and connect a TerminusDB client using app settings.

    Returns:
        A connected Client bound to the configured database.
    """
    settings = get_settings()
    client = Client(settings.TERMINUS_HOST)
    # Connect to the target database.
    # If the DB doesn't exist yet, create it first.
    try:
        client.connect(db=settings.TERMINUS_DB,
                       user=settings.TERMINUS_USER,
                       key=settings.TERMINUS_KEY,
                       team=settings.TERMINUS_TEAM,)
    except Exception:
        client.create_database(
            settings.TERMINUS_DB,
            label=settings.TERMINUS_DB,
            description="V-NOC code analysis graph",
        )
        client.connect(db=settings.TERMINUS_DB,
                       user=settings.TERMINUS_USER,
                       key=settings.TERMINUS_KEY,
                       team=settings.TERMINUS_TEAM,)

    return client


def get_terminus_client() -> Client:
    """
    Return a cached, singleton TerminusDB Client.

    This replaces `get_db_async_client()` from the ArangoDB version.
    """
    global _client
    if _client is None:
        _client = _build_client()
    return _client


# FastAPI dependency (mirrors the old `get_db` function signature)
async def get_db() -> Client:
    """
    FastAPI dependency: returns the TerminusDB client.

    Kept as `get_db` for compatibility — repos that previously did:
        db = Depends(get_db)
    will still work, but `db` is now a Client, not AsyncDatabase.
    """
    return get_terminus_client()


def close_db_client() -> None:
    """Close the global TerminusDB client (best-effort)."""
    global _client
    try:
        if _client is not None:
            _client.close()
    finally:
        _client = None
