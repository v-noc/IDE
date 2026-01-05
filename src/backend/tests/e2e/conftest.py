import pytest
import pytest_asyncio
import shutil
from httpx import AsyncClient, ASGITransport
from arango.database import StandardDatabase

from app.main import app
from pathlib import Path
from app.db.client import get_db
from app.core.services.project_service import ProjectService


@pytest_asyncio.fixture()
async def client(arangodb_client: StandardDatabase) -> AsyncClient:
    """
    Provides an AsyncClient instance for making API requests, with the database
    dependency overridden to use the test database.
    """

    def override_get_db():
        return arangodb_client

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def sample_project_path(tmp_path):
    """Returns the path to a temporary copy of the sample project directory for E2E tests."""
    source_path = Path(__file__).parent / "core/sample_project"
    project_path = tmp_path / "sample_project"
    shutil.copytree(source_path, project_path)
    return str(project_path)


@pytest_asyncio.fixture
async def sample_project_node(create_repos):
    """Returns the sample project node for E2E tests."""

    project_service = ProjectService(create_repos)
    return await project_service.create(
        "sample_project",
        "A sample project for E2E tests",
        "sample/path"
    )


@pytest_asyncio.fixture
async def created_sample_project(create_repos):
    project_service = ProjectService(create_repos)
    return await project_service.create(
        "sample_project",
        "A sample project for E2E tests",
        "sample/path"
    )
