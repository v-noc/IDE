import pytest
import sys
from unittest.mock import MagicMock

try:
    from arango import DatabaseDeleteError
    from arango.client import ArangoClient
    from app.db.client import get_db
    ARANGO_AVAILABLE = True
except ImportError:
    ARANGO_AVAILABLE = False
    # Mock arango globally
    import types
    arango_mock = types.ModuleType("arango")
    sys.modules["arango"] = arango_mock
    
    sys.modules["arango.database"] = MagicMock()
    sys.modules["arango.client"] = MagicMock()
    sys.modules["arango.collection"] = MagicMock()
    sys.modules["arango.exceptions"] = MagicMock()
    
    DatabaseDeleteError = Exception
    ArangoClient = MagicMock()
    get_db = MagicMock()

# Import app modules AFTER mocking
from app.core.repository import Repositories


TEST_DB_NAME = "test_db"


@pytest.fixture()
def arangodb_client():
    if not ARANGO_AVAILABLE:
        yield MagicMock()
        return

    client = get_db()

    # 2. Create a new database for the test session if it doesn't exist
    if not client.has_database(TEST_DB_NAME):
        client.create_database(TEST_DB_NAME)

    # 3. Yield a new client instance connected to the test database
    # This is the object your tests will interact with.
    _client = ArangoClient("http://localhost:8529")
    test_db_client = _client.db(
        TEST_DB_NAME,
        username="root",
        password="password"
    )
    yield test_db_client

    # 4. Teardown: after all tests are done, drop the test database
    # The `sys_db` client is used again for its administrative privileges.

    try:
        client.delete_database(TEST_DB_NAME, ignore_missing=True)
    except DatabaseDeleteError:
        print(
            f"Failed to delete the test database '{TEST_DB_NAME}'. It may require manual cleanup.")


@pytest.fixture
def create_repos(arangodb_client):
    return Repositories(arangodb_client)
