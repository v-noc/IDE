
from arangoasync import ArangoClient
from arangoasync.auth import Auth
from arangoasync.database import AsyncDatabase


from ..config.settings import get_settings

# Global variables to hold the client and connection


async def get_db_async_client() -> AsyncDatabase:
    global _client, _db_connection
    settings = get_settings()

    async with ArangoClient(hosts=settings.ARANGO_HOST) as client:
        auth = Auth(username=settings.ARANGO_USER,
                    password=settings.ARANGO_PASSWORD)
        db = await client.db(settings.ARANGO_DB, auth=auth)
        return db

# For application-level dependency injection, if needed
