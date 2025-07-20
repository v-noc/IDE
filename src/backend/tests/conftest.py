# tests/conftest.py

import pytest
from arango import ArangoClient
from app.config.settings import settings
import time

@pytest.fixture(scope="session")
def test_db_name():
    """Generate a unique test database name for the entire test session."""
    return f"test_db_{int(time.time())}"

@pytest.fixture(scope="session")
def arango_client():
    """Provides a client to the ArangoDB instance for the test session."""
    return ArangoClient(hosts=settings.ARANGO_HOST)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database(arango_client, test_db_name):
    """
    Creates a new database for the test session, yields a connection to it,
    and then tears it down at the end of the session.
    """
    sys_db = arango_client.db("_system", username="root", password="password")
    if not sys_db.has_database(test_db_name):
        sys_db.create_database(test_db_name)

    # Create the user if it doesn't exist
    if not sys_db.has_user(settings.ARANGO_USER):
        sys_db.create_user(
            username=settings.ARANGO_USER,
            password=settings.ARANGO_PASSWORD,
            active=True
        )

    # Grant permissions to the app user for the new database
    sys_db.update_permission(
        username=settings.ARANGO_USER,
        database=test_db_name,
        permission="rw"
    )

    # Monkeypatch the settings to use the test database
    original_db_name = settings.ARANGO_DB
    settings.ARANGO_DB = test_db_name

    yield # Run all tests

    # Teardown: drop the test database
    settings.ARANGO_DB = original_db_name
    if sys_db.has_database(test_db_name):
        sys_db.delete_database(test_db_name)

@pytest.fixture
def temp_project_dir(tmp_path):
    """
    Creates a temporary directory with a sample project structure for a single test.
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    
    (project_dir / "utils").mkdir()

    (project_dir / "main.py").write_text(
        "from utils.helpers import helper_func\n\n"
        "class MainApp:\n"
        "    def run(self):\n"
        "        helper_func()\n\n"
        "def start_app():\n"
        "    app = MainApp()\n"
        "    app.run()\n"
    )

    (project_dir / "utils" / "helpers.py").write_text(
        "def helper_func():\n"
        "    print('Hello from helper!')\n"
    )
    
    yield str(project_dir)
