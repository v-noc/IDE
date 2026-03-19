import pytest
import shutil
from pathlib import Path
from app.db.context import RequestDbContext, ProjectUoW
from app.core.services.project_service import ProjectService
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator
import pytest_asyncio


@pytest.fixture
def sample_project_path(tmp_path):
    """Returns the path to a temporary copy of the sample project directory for E2E tests."""
    source_path = Path(__file__).parent / "sample_project"
    project_path = tmp_path / "sample_project"
    shutil.copytree(source_path, project_path)
    return str(project_path)


@pytest_asyncio.fixture
async def built_sample_project(sample_project_path, terminusdb_client):
    """Creates a project and runs GraphBuilder to populate structure (no API)."""
    ctx = RequestDbContext()
    project_uow = ProjectUoW(terminusdb_client, None, ctx)
    project_service = ProjectService(project_uow)
    print(f"Creating sample project at: {terminusdb_client.db}")
    project_node = await project_service.create(
        "sample_project",
        "A sample project for E2E tests",
        sample_project_path,
    )

    project_uow = ProjectUoW(terminusdb_client, project_node, ctx)
    orchestrator = GraphBuilderOrchestrator(
        project_node=project_node,
        uow=project_uow,
        ignore_file_name=".gitignore",
    )
    await orchestrator.resync()
    yield project_node, project_uow

    await project_service.delete(project_node.id)
