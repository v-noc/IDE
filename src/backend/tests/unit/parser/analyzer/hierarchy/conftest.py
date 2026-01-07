import pytest_asyncio
import shutil
from pathlib import Path

from app.core.model.nodes import ProjectNode
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator
from app.core.repository import Repositories
from app.core.services.project_service import ProjectService

# Fixture projects for different test types
FIXTURE_PROJECT_FOLDER = Path(__file__).parent / "test_folder"
FIXTURE_PROJECT_FILE = Path(__file__).parent / "test_file"
FIXTURE_PROJECT_STRUCTURE = Path(__file__).parent / "test_structure"
PROJECT_NAME_FOLDER = "test_folder"
PROJECT_NAME_FILE = "test_file"
PROJECT_NAME_STRUCTURE = "test_structure"


@pytest_asyncio.fixture
async def setup_folder_project(tmp_path, arangodb_client):
    """Setup project for folder tests with multiple folders."""
    project_path = tmp_path / "project"
    shutil.copytree(FIXTURE_PROJECT_FOLDER, project_path)

    project_node = ProjectNode(
        name=PROJECT_NAME_FOLDER,
        path=str(project_path),
        qname=PROJECT_NAME_FOLDER,
        description="Test Project for Folder Operations",
    )

    repos = Repositories(arangodb_client)
    await repos.ensure_collections()

    project_service = ProjectService(repos)
    project_node = await project_service.create_node(project_node)

    return project_node, repos, arangodb_client, project_path


@pytest_asyncio.fixture
async def setup_file_project(tmp_path, arangodb_client):
    """Setup project for file tests with multiple files."""
    project_path = tmp_path / "project"
    shutil.copytree(FIXTURE_PROJECT_FILE, project_path)

    project_node = ProjectNode(
        name=PROJECT_NAME_FILE,
        path=str(project_path),
        qname=PROJECT_NAME_FILE,
        description="Test Project for File Operations",
    )

    repos = Repositories(arangodb_client)
    await repos.ensure_collections()

    project_service = ProjectService(repos)
    project_node = await project_service.create_node(project_node)

    return project_node, repos, arangodb_client, project_path


@pytest_asyncio.fixture
async def setup_structure_project(tmp_path, arangodb_client):
    """Setup project for structure tests with both folders and files."""
    project_path = tmp_path / "project"
    shutil.copytree(FIXTURE_PROJECT_STRUCTURE, project_path)

    project_node = ProjectNode(
        name=PROJECT_NAME_STRUCTURE,
        path=str(project_path),
        qname=PROJECT_NAME_STRUCTURE,
        description="Test Project for Structure Operations",
    )

    repos = Repositories(arangodb_client)
    await repos.ensure_collections()

    project_service = ProjectService(repos)
    project_node = await project_service.create_node(project_node)

    return project_node, repos, arangodb_client, project_path


async def _build_and_get_tree(project_node, repos, db):
    """Helper function to build project and get tree structure."""
    orchestrator = GraphBuilderOrchestrator(
        project_node,
        db=db,
        ignore_file_name="v-noc.toml",
    )
    await orchestrator.resync()

    project_service = ProjectService(repos)
    project = await project_service.get(project_node.id)
    assert project is not None, "Project not found after build"

    children = await project_service.get_children(project_node.id)
    from app.core.builder.tree_builder import TreeBuilder
    tree_builder = TreeBuilder(children)
    return tree_builder.build()
