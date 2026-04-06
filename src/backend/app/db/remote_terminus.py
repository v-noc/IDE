from contextlib import asynccontextmanager
from typing import AsyncIterator

from app.db.async_terminus_client import AsyncClient


@asynccontextmanager
async def remote_terminus_client(
    server_url: str,
    *,
    user: str,
    key: str,
    team: str,
) -> AsyncIterator[AsyncClient]:
    """Connected admin client (no DB selected) for remote create/bootstrap."""
    client = AsyncClient(server_url.rstrip("/"))
    try:
        await client.connect(
            team=team,
            db=None,
            user=user,
            key=key,
            branch="main",
        )
        yield client
    finally:
        await client.close()
