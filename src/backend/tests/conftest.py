# tests/conftest.py
import os
import pytest
import time
from pathlib import Path

def pytest_configure(config):
    """
    This hook runs before pytest collects any tests.
    It sets the necessary environment variables to ensure the application
    loads the test configuration.
    """
    os.environ["APP_ENV"] = "test"
    conftest_dir = Path(__file__).parent
    env_file_path = conftest_dir / ".env.test"
    os.environ["ENV_FILE"] = str(env_file_path)

# --- Fixtures ---

@pytest.fixture(scope="session")
def monkeypatch_session():
    """Session-scoped monkeypatch."""
    from _pytest.monkeypatch import MonkeyPatch
    m = MonkeyPatch()
    yield m
    m.undo()

@pytest.fixture(scope="session")
def test_settings():
    """
    Returns the application settings for the test environment.
    """
    from app.config.settings import get_settings
    return get_settings()

@pytest.fixture(scope="session")
def test_db_name():
    """Generate a unique, session-scoped test database name."""
    return f"test_db_{int(time.time())}"

@pytest.fixture(scope="session", autouse=True)
def setup_test_database(test_settings, test_db_name, monkeypatch_session):
    """
    Set up the test database for the entire test session.
    """
    from arango import ArangoClient

    monkeypatch_session.setattr(test_settings, "ARANGO_DB", test_db_name)

    sys_client = ArangoClient(hosts=test_settings.ARANGO_HOST)
    sys_db = sys_client.db(
        "_system",
        username="root",
        password=test_settings.ARANGO_ROOT_PASSWORD
    )

    if not sys_db.has_user(test_settings.ARANGO_USER):
        sys_db.create_user(
            username=test_settings.ARANGO_USER,
            password=test_settings.ARANGO_PASSWORD,
            active=True
        )

    if not sys_db.has_database(test_db_name):
        sys_db.create_database(test_db_name)

    sys_db.update_permission( # This was the error
        username=test_settings.ARANGO_USER,
        database=test_db_name,
        permission="rw"
    )
    
    yield

    if sys_db.has_database(test_db_name):
        sys_db.delete_database(test_db_name, ignore_missing=True)

@pytest.fixture(scope="function", autouse=True)
def clean_collections():
    """
    Function-scoped fixture to ensure a clean state for each test.
    """
    from app.db.client import get_db
    
    db = get_db()
    for collection in db.collections():
        if not collection["system"]:
            db.collection(collection["name"]).truncate()
    yield

@pytest.fixture
def temp_project_dir(tmp_path):
    """Creates a temporary directory with a sample project structure."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("print('hello from test project')")
    yield str(project_dir)