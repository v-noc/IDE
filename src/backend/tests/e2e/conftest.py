import pytest
import pytest_asyncio
import shutil
from httpx import AsyncClient, ASGITransport

from app.main import app
from pathlib import Path
from app.db.client import get_terminus_client
from app.core.services.project_service import ProjectService
from app.db.async_terminus_client import AsyncClient as TerminusClient
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator


@pytest_asyncio.fixture()
async def client(terminusdb_client: TerminusClient) -> AsyncClient:
    """
    Provides an AsyncClient instance for making API requests, with the database
    dependency overridden to use the test database.
    """

    async def override_get_db():
        return terminusdb_client

    app.dependency_overrides[get_terminus_client] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as c:
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
async def built_sample_project(sample_project_path, create_repos, terminusdb_client):
    """Creates a project and runs GraphBuilder to populate structure (no API)."""
    project_service = ProjectService(create_repos)
    print(f"Creating sample project at: {create_repos.client.db}")
    project_node = await project_service.create(
        "sample_project",
        "A sample project for E2E tests",
        sample_project_path,
    )

    clone_db = terminusdb_client.clone()
    orchestrator = GraphBuilderOrchestrator(
        project_node=project_node,
        db=clone_db,
        ignore_file_name=".gitignore",
    )
    await orchestrator.resync()
    yield project_node, create_repos

    await project_service.delete(project_node.id)


@pytest_asyncio.fixture
async def sample_project_node(empty_project_uow):
    """Returns the sample project node for E2E tests."""

    project_service = ProjectService(empty_project_uow)
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
