import pytest
import pytest_asyncio

from arangoasync import ArangoClient
from arangoasync.auth import Auth
from arangoasync.database import AsyncDatabase

from app.core.repository import Repositories


TEST_DB_NAME = "test_db"


@pytest_asyncio.fixture(scope="function")
async def arangodb_client() -> AsyncDatabase:
    # Create one async client for the test session.
    client = ArangoClient(hosts="http://localhost:8529")
    await client.__aenter__()

    auth = Auth(username="root", password="password")

    # Use _system for DB administration.
    sys_db = await client.db("_system", auth=auth)
    if not await sys_db.has_database(TEST_DB_NAME):
        await sys_db.create_database(TEST_DB_NAME)

    test_db = await client.db(TEST_DB_NAME, auth=auth)
    yield test_db

    # Teardown: drop the test DB.
    try:
        await sys_db.delete_database(TEST_DB_NAME, ignore_missing=True)
    except Exception as e:
        print(
            (
                f"Failed to delete the test database '{TEST_DB_NAME}'. "
                f"It may require manual cleanup. Error: {e}"
            )
        )
    finally:
        # python-arango-async's close is async; ensure resources are awaited.
        await client.close()


@pytest.fixture
def create_repos(arangodb_client):
    return Repositories(arangodb_client)
