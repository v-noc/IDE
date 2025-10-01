import pytest
from fastapi.testclient import TestClient
from arango.database import StandardDatabase

from app.main import app
from pathlib import Path
from app.db.client import get_db


@pytest.fixture()
def client(arangodb_client: StandardDatabase) -> TestClient:
    """
    Provides a TestClient instance for making API requests, with the database
    dependency overridden to use the test database.
    """

    def override_get_db():
        return arangodb_client

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def sample_project_path():
    """Returns the path to the sample project directory for E2E tests."""
    return str(
        Path(__file__).parent
        / "core/sample_project"
    )
