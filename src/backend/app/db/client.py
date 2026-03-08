"""
TerminusDB async client module.

Provides a singleton AsyncClient instance with proper lifecycle
management for use with FastAPI.
"""

from .async_terminus_client import AsyncClient
from ..config.settings import get_settings
from app.core.model.schemas import ProjectSchema, BaseSchema, TerminusBase, ThemeConfigSchema
from app.db.woqlschema import *

_client: AsyncClient | None = None


async def migrate_base(client):
    schema_obj = WOQLSchema(
        title="V-NOC Schema",
        description="V-NOC code analysis graph schema",
        authors=["V-NOC Team"],
    )
    schema_obj.add_obj(TerminusBase.__name__, TerminusBase)
    schema_obj.add_obj(BaseSchema.__name__, BaseSchema)
    schema_obj.add_obj(ThemeConfigSchema.__name__, ThemeConfigSchema)
    schema_obj.add_obj(ProjectSchema.__name__, ProjectSchema)
    await schema_obj.commit(client, "Add ProjectSchema to schema", full_replace=True)


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
            dbid=settings.TERMINUS_DB,
            team=settings.TERMINUS_TEAM,
            label=settings.TERMINUS_DB,
            description="V-NOC code analysis graph",
        )
        await client.connect(
            db=settings.TERMINUS_DB,
            user=settings.TERMINUS_USER,
            key=settings.TERMINUS_KEY,
            team=settings.TERMINUS_TEAM,
        )
    await migrate_base(client)
    return client


async def get_terminus_client() -> AsyncClient:
    global _client
    if _client is None:
        _client = await _build_client()
    return _client


async def close_db_client() -> None:
    global _client
    try:
        if _client is not None:
            await _client.close()
    finally:
        _client = None
