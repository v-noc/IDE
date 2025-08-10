import pytest
from fastapi.testclient import TestClient
from app.main import app
from pathlib import Path


@pytest.fixture(scope="session")
def client() -> TestClient:
    """
    Provides a TestClient instance for making API requests.
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def sample_project_path():
    """Returns the path to the sample project directory for E2E tests."""
    # Note: This assumes the test is run from the project root.
    # We navigate from the root to the unit test's sample_project.
    return str(
        Path(__file__).parent.parent
        / "unit/core/parser/sample_project"
    ) 